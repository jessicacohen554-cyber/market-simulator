# Market Simulation Model — Methodology Specification

> Status: **FINALIZED** 2026-09-05 (model-audit program WS4 / DOCS-B, gate G2).
> This document describes the **shipped** model. It is no longer a build
> specification: the Phase-0 build-agent instructions, the never-met performance
> targets and the as-built patch notes were retired at finalization, and the
> governance rules it used to restate now live only in `CLAUDE.md`, cited here by
> stable `[R-*]` ID. Execution record:
> `docs/handoffs/methodology-finalization-audit-2026-08.md`.

**Purpose:** Methodology specification for the LP-based electricity market dispatch model. This document governs the model’s mathematical formulation, computational patterns and scenario architecture. It is the primary reference for how the model works; where this document and the code disagree, the **code is the source of truth** — open a `/sync-docs` pass to reconcile.

**Scope:** Multi-ISO hourly dispatch over a 2026–2050 forecast trajectory, with a historical-backcast mode for calibration. Nine regions are registered in `config/iso_configs.py` — ERCOT (7 zones, 6 carry load), CAISO (5 in-state zones + WECC import node), PJM (8 zones), MISO (6 zones), NYISO (5 zones), NEISO (4 load zones + HQ import node), SPP (2 zones), NWPP (5 whole-BA zones over a 17-BA pool) and SOCO (3 zones, a single balancing authority with no LMP market) — sharing one ISO-agnostic LP. ERCOT is the fully-calibrated reference; the others have topology and plant-to-zone assignment but varying data/backcast maturity (see `docs/multi-iso/`). Parameterized scenario system supporting batch sweeps and single custom runs.

**Forecast vs. backcast.** The model is fundamentally a **forecasting** tool (2026→2050). A *backcast* mode reruns a historical weather year against actuals (EIA-930, CAMPD, eGRID, EIA-923) to calibrate parameters. The switch is the explicit **`ScenarioConfig.mode`** field (`"forecast"` default / `"backcast"`, Tier 0) — never inferred from other parameters (it used to ride on `gas_price_override`, which wrongly flipped any pinned-gas forecast sensitivity into backcast behavior). Several mechanisms — historic outage overlays, F923 delivered fuel prices, **same-year** plant-specific CEMS emission rates, weather-year pinning — are **backcast/calibration devices only**; forecast runs use the statistical/parametric models (forecast-year CO2 rates for existing units are instead *derived from* multi-year CAMPD history, §3.3 — a measured input, not a same-year overlay). This distinction is called out throughout; do not conflate the two.

**Runtime:** Python 3.11+. Solver: HiGHS via `highspy`. No Pyomo, no PuLP, no scipy.optimize.

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

The **dual variable on this constraint = zonal price ($/MWh)**. This is the model’s primary price output, and rule 4 `[R-DUALS]` makes it the *only* one — there is no separate pricing model anywhere in the production path (§1.9).

> **A note on module citations.** The dispatch LP was split out of
> `model/dispatch.py` into the `model/lp/` package on 2026-07-22
> (`layout` / `costs` / `rows` / `reserve_rows` / `bounds` / `model`), and
> `model/transmission.py` was likewise split into `model/interchange/`. Both
> original modules survive as **facades that alias themselves to their package**,
> so every historical import path, `mock.patch` target and pickled module path
> keeps resolving — that import surface is **frozen** by the pickle/module-path
> identity contract, deliberately, not by neglect. This document therefore cites
> each name at its **physical home** (`model/lp/rows.py::build_constraints`, not
> `dispatch.build_constraints`) while the facade spelling remains valid in code.

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
`model/lp/bounds.py`): under `caiso_storage_as_reservation` (GATED, default off,
backcast) CAISO battery SOC is floored at the tariff 30-minute sustain of the
measured spin/non-spin award and the battery power cap is derated by the
measured upward award (`model/storage.py::reserve_caiso_storage_as_power`,
the ERCOT `storage_as_commitment` pattern). The caiso-74 probe measured this
reservation **ex-ante inert** on CAISO's zone-aggregate fleet (the LP
discharges 3.7–6 GW below the nameplate cap), so it is not part of any keeper
recipe — see `results/calibration/FINDING-caiso74-storage-as-reservation-2026-07-11.md`.

No hard cycling-limit constraint, but cycling is no longer free: beyond the ε tiebreaker, each storage unit's discharge slot can carry a per-unit dispatch cost (`StorageUnit.vom` → `build_cost_vector(storage_discharge_cost=...)`, `model/lp/costs.py`). Two reduced-form throughput costs use it, both standing in for real economics the energy-only LP otherwise ignores (cycling degradation plus ancillary-service/reserve opportunity cost): pumped storage *can* carry a per-ISO calibrated adder (`resolve_pumped_storage_dispatch_adder`, `constants.PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`), though that registry is currently **empty** (`{}`) so every ISO resolves to 0.0 — the former PJM $10/MWh adder was retired per rule 13 `[R-MEASURED]` (it had been fitted to a *mis-measured* residual; the in-code comment at `constants.py` documents the round-trip-loss vs. gross-discharge measurement error in full), and grid batteries carry `ScenarioConfig.battery_dispatch_adder` (Tier 3, default 0; the ERCOT backcast keeper sets $10/MWh, landing 2025 battery discharge within −1.5% of the EIA-930 measured 5.44 TWh where the un-priced LP over-cycled +48% — see `docs/calibration-log.md`, ERCOT E2 entry). The original "flag for future sensitivity if unrealistic cycling appears" fired and was resolved by these adders. Both solve paths (forecast `runner.py` and backcast `scripts/run_calibration.py`) pass `storage_discharge_cost=storage.vom`, so the throughput adders are active in all dispatch modes.

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

**Marginal transmission losses** (`ScenarioConfig.miso_zonal_loss_surface`,
tier 3, GATED default off — MISO-scoped per rule 25 `[R-ISO-SCOPE]`): each Midwest-internal
bidirectional link (L1–L6) splits into a one-way pair
(`transmission.apply_miso_zonal_loss_links`, the RDT pair's structure plus a
0.001 $/MWh flow tiebreak of the storage-ε class), and each direction's
RECEIVING-end energy-balance coefficient becomes `1 − eps(month)`
(`transmission.build_miso_link_loss` → `lp/rows.build_constraints(link_loss)`,
an hour-varying sparse correction on the kron balance). The loss fraction
`eps_(x→y),m = max(0, (dev_y − dev_x)/(1 + dev_y))` comes from the
dimensionless per-zone monthly marginal delivery-factor deviation surface
derived from MISO's own published per-hub LMP components (MLC = MEC × (DF−1);
frozen derive `scripts/data/derive_miso_loss_surface.py`, DA basis; per-year
rows for backcast train years — the same-year measured-physical class as CEMS
rates — and pooled rows for forecast years). Transported energy then consumes
MWh and interior uncongested duals separate by exactly the measured
delivery-factor ratio `λ_y/λ_x = (1+dev_y)/(1+dev_x)` — prices stay LP duals
(never an adder), zero fitted scalars. The reverse direction of each pair
clamps to zero loss (the marginal-DF linearization is oriented by the month's
persistent gradient; atypical-direction hours carry no separation rather than
a fabricated inverted one — a documented conservative under-transmission).
Adjudication: the miso-76 A/B (2026-07-19) was a REJECTED PROBE under its
frozen charter's pre-registered R2 (an East-2025 cancellation pair-year the
loss-only mechanism cannot represent; the offsetting congestion component is
the data-blocked M4 gap), so the flag ships default-off in every keeper; see
`docs/handoffs/miso-nc-price-separation-design-2026-07.md` and the
2026-07-19 miso-76 calibration-log entry.

**Aggregate interface groups** (`InterfaceLimit`, `iso_configs.py`): one row
per group per hour caps the **signed sum** of member-link flows. Each listed
``(from, to)`` pair pulls in EVERY link joining that zone pair — matching
orientation with sign +1, reversed with −1 — so the sum reads as the net
corridor flow in the listed direction, and an opposing one-way pair (the RDT)
contributes ``flow(a→b) − flow(b→a)`` from one listed pair. ``cap_mw`` bounds
the positive direction; the optional ``reverse_cap_mw`` sets an asymmetric
reverse bound (import CIL vs export CEL); caps may be scalars or hourly
``(T,)`` vectors (seasonal envelopes). Implemented in
`transmission.build_interface_groups` → `lp/rows._build_interface_rows`.

The topology (zones, load shares, links, TTCs) is per-ISO data in `config/iso_configs.py`; the LP itself is ISO-agnostic and reads `n_zones`, `n_links`, the node–link `incidence` matrix, and per-link `ttc`. Current topologies:

- **ERCOT** — 7 zones (West, Panhandle, North, Northeast, Houston, South_Central, South; Panhandle carries 0 load), 10 links, with cited inter-zone TTCs. The reference calibration.
- **CAISO** — 5 in-state zones, **plus** a WECC import/export node (see below); 6 links + 1 interface limit (`WECC_import_simultaneous`). North of Path 26 the historical north–south split stands — **NP15** (north of Path 15) and **ZP26** (between Path 15 and Path 26). South of Path 26 the former single `SP15` zone was split (2026-07-09) into its three **local capacity areas**: **LA_BASIN** (the SCE LA-basin LCR pocket, Big Creek/Ventura folded in), **SDGE** (the SDG&E / Path-44 pocket, post-SONGS import-limited) and **SP15_rest** (the residual south gateway that Path 26 and Path 46/WOR feed, and from which the two pockets import over import-limited one-way links). The split exists because a single copperplate SP15 cannot form the LA-basin/SDG&E congestion premium the CAISO LCT study's local capacity areas set. The three children's load shares are measured from the LCT study's published pocket peaks (LA_BASIN 0.374, SDGE 0.091) with `SP15_rest` the exact residual (0.0735), so they sum to the old SP15 share of 0.5385 — `validate_topology` hard-errors otherwise. See `config/iso_configs.py::_caiso_config` and `docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md`.
- **PJM** — 8 aggregated zones (`PJM_ComEd`, `PJM_AEP_Ohio`, `PJM_ATSI`, `PJM_West_APS`, `PJM_Central_PA`, `PJM_Dominion`, `PJM_EMAAC`, `PJM_SWMAAC`), 11 links, rolling up PJM's 20+ transmission zones onto the chronic west→Mid-Atlantic congestion corridors.
- **MISO** — 6 zones drawn as whole EIA-930 sub-BA (LRZ-union) partitions — `MISO-West` (LRZ 1), `MISO-Plains` (LRZ 3+5), `MISO-Illinois` (LRZ 4), `MISO-Indiana` (LRZ 6), `MISO-East` (LRZ 2+7), `MISO-South` (LRZ 8+9+10) — 8 links: 6 deliberately non-binding internal pipes plus the RDT one-way contract-path pair (3,000 MW N→S / 2,500 MW S→N) attached to `MISO-Plains`. Internal congestion is carried by per-zone directional CIL/CEL `InterfaceLimit` groups from the MISO LOLE Study Reports (static PY2025-26 summer caps in config; backcasts replace them with per-season hourly vectors via `transmission.build_miso_deliverability_groups`). See `docs/multi-iso/miso-zonal-refinement-scope.md`.
- **NYISO** — 5 zones (Upstate_West, Capital_Hudson, Lower_Hudson, NYC, Long_Island) with nested downstate import cutsets.
- **NEISO** — 4 load zones (North, Central, Boston, Connecticut) **plus** an HQ import node; 7 links.

CAISO's WECC import/export node is modeled as **pseudo-generators on a stepped supply curve**:

- Import tranches: 3–4 blocks with increasing marginal cost and MW limits (e.g., PNW hydro cheap/limited, Desert SW CCGT mid, Desert SW CT expensive). These are `P[g,t]` variables assigned to the WECC “zone” with their own cost and capacity.
- Export: allow CAISO to push power to the import node at a cost of zero or small negative (represents dumping surplus solar).
- Aggregate limit: ~12–15 GW import, ~5 GW export. Derive from EIA-930 interchange data.

**Forward per-hub seam (forecast-native, 2026-06).** The static stepped ladder is a backcast fit. For a forecast the WECC node is split into the two real corridors (COI/Path-66 → Malin/WECC_PNW → NP15; Path-46/WOR → Palo Verde/WECC_DSW → SP15), each priced by the **reference-price interface** (the same construction PJM/MISO use): `per-hub price = (henry_hub[year] + gas_basis) × marginal_heat_rate × load_shape`, with the solar-driven desert-SW on a **net-load** shape so its midday price dips with the solar glut. The corridor import cap is a forward ATC = `TTC × posted-ATC fraction × forward solar derate` (not the measured p95 flow). Flags `caiso_intertie_reference_price` / `caiso_corridor_atc_forward` (require `caiso_per_hub_intertie`); the measured WECC hub LMP + p95 envelope are retained only as the backcast realization the formula is validated against. See `docs/forecast-methodology-gaps-2026-06.md` G8 and `data/neighbor_price.caiso_hub_reference_price` / `model/transmission.forward_corridor_atc_envelope`.

**NEISO measured seam ladders (2026-07-06, audit C-6 closure).** NEISO's static ladders are no longer residual-fitted: `IMPORT_TRANCHES[_BY_YEAR]["NEISO"]` / `EXPORT_TRANCHES[_BY_YEAR]["NEISO"]` are derived by a frozen formula (`scripts/data/derive_neiso_import_tranches.py`) from measured data only — per-seam Q-Q duration coupling of the measured ISO-NE DA hub LMP with the measured EIA-930 per-seam flows (HQT/NBSO/NYIS), rung capacities at the measured p98 per-seam depth (Highgate carved at its published ~225 MW rating), NYISO proxy-bus anchors (`NYISO_HQ` = HQ's opportunity cost, `NYISO_NPX` = NY-side interface price) reported per rung, and export sinks clamped below the cheapest import rung (the pooled `HQ_import` node cannot host wheel-through counterflow — rule 14 `[R-ACCURATE]` reconciliation). Backcast years resolve year-keyed ladders on BOTH sides of the node (`EXPORT_TRANCHES_BY_YEAR` mirrors `IMPORT_TRANCHES_BY_YEAR` through `get_interchange_spec` / `build_export_sinks`, interchange_config.py); forecast years carry the pooled 2023-2025 ladder. Rule 23 `[R-FROZEN-DERIVE]` frozen: re-derive only when the source data extends.

**MISO measured seam ladders (2026-07-07, audit C-6 closure for MISO — the G-23-residual import-starvation fix).** Under `ScenarioConfig.miso_seam_measured_ladder` (backcast opt-in), every band of MISO's reference-price seams (PJM/SPP/South, import + export) is repriced by `transmission.inject_miso_seam_ladder_prices` to the measured per-year Q-Q ladder in `interchange_config.MISO_SEAM_LADDER_BY_YEAR` — the same NEISO construction (`scripts/data/derive_miso_seam_ladders.py`) on the existing 8-band grid: band *k*'s price is the measured MISO **DA** hub LMP quantile whose exceedance duration equals the measured EIA-930 duration of the seam flowing deeper than the band's midpoint (export side mirrored); no hurdle is added (the revealed thresholds embed delivery costs). Band capacities and the measured (month × hour-of-day) seam envelopes are unchanged. Why: the measured PJM+IESO seam flow is a firm/scheduled base — importing in ~98–100% of hours, hourly-uncorrelated with the spread (r ≈ +0.06), 2025 mean RT spread $0.00 while 28 TWh flowed — which the hurdle-gated spot-spread formula structurally deletes in a zero-spread year (`docs/multi-iso/miso-import-starvation-rootcause-2026-07.md`). The ladder never forces flow (contrast the rejected `miso_firm_import_floor` pin): every band clears economically against the model's own hourly price. Forecast years keep the gas-elastic reference-price formula (the `hr_by_year` two-track design; the pooled 2023–2025 ladder printed by the derive script is the forward story). Rule 23 `[R-FROZEN-DERIVE]` frozen: re-derive only when the source data extends.

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

**RPS (active):** When `rps_enabled` is set and the ISO has an RPS floor for the year, the dispatch LP appends one annual constraint row requiring the statute's renewable-tier eligible generation to reach `rps_target` of total demand. The target is the statute's RENEWABLE tier (`STATE_RPS_FLOORS` — never a nuclear-counting clean/zero-emission tier, FFR-7B Arm 1), and the eligible set is the statute's (`RPS_ELIGIBLE_FUELS_BY_ISO`, cited per ISO): the wind/solar zone columns always count, and any further statutorily-eligible classes (NYISO existing hydro; CAISO geothermal/biomass; offshore wind where present) enter via their thermal-block dispatch columns. **Nuclear is never eligible** (CX-6a — counting it would crush the REC dual; nuclear's zero-emission support flows through `eac_price_nuclear`/CES instead; the spec's original nuclear-counting formulation is superseded):

```
# RPS constraint (annual)
Σ_z Σ_t (W[z,t] + S[z,t]) + Σ_{g∈eligible non-W/S classes} Σ_t P[g,t] (+ Σ_t ACP[t])
    ≥ rps_target × Σ_z Σ_t Demand[z,t]

Dual on this constraint = REC price ($/MWh), capped at the ACP ceiling by the
escape column, which feeds into the economic new entry screen as additional
clean energy revenue.
```

The constraint creates a shadow price that raises clean revenue and compresses thermal margins, so clean additions and thermal retirements are driven entirely through the economic screens — no force-build in capacity evolution.

**Per-state compliance-region grain (MISO only — FFR-7B Arm 2 / FFR-6B E-1, GATED `miso_rps_compliance_regions`, default off).** The single ISO-wide row silently asserts free intra-ISO REC trade — true in PJM/NEISO/NYISO/CAISO (footprint-wide REC eligibility / one obligated state, so their one row is arithmetically exact) and false in MISO (MCL 460.1029 restricts Michigan credits to in-state systems; CEJA procures centrally; MN's standard is delivered-to-MN-retail). Armed, the ISO-wide row is REPLACED by K per-state rows (`MISO_RPS_COMPLIANCE_REGIONS`: MN/MI/WI/IL/MO; MT excluded, its ±.0345 bracket recorded open): for each region `r`, `Σ_{z∈eligible(r)} Σ_t (W+S) + Σ_t ACP_r[t] ≥ Σ_z w_{r,z}·target_r·Σ_t Demand[z,t]`, each with its OWN ACP escape ($30 MISO proxy). Row `r`'s dual is compliance market `r`'s REC price; `rps_shadow_price` becomes the per-zone consumer vector `p[z] = max{dual_r : z ∈ eligible(r)}`, resolved at each candidate's/unit's zone by every capacity screen (`policy.rps.rps_credit_for_zone`) — a broadcast scalar would credit MISO-East's dual to an Arkansas candidate. `K=1`/mask=all reproduces the single row byte-identically (regression-tested). The rows' only output is a price — E-1 never acquires a build limb.

**Clean/carbon-free tier row family (MISO West/East — FFR-7B Arm 3 / FFR-6B E-2, GATED `miso_clean_tier_rows`, default off; requires the Arm-2 family).** A SECOND, independent row family on the same machinery — never a widening of the renewable row (a state with both tiers gets two rows). Two rows (`MISO_CLEAN_TIER_REGIONS`): MN carbon-free (Minn. Stat. §216B.1691 subd. 2g — 80/90/100% by 2030/35/40; qualifying set includes hydrogen and biomass) and MI clean (2023 PA 235 — 80% by 2035, 100% by 2040; qualifying admits qualified CCS gas; MISO-East-only eligibility). Illinois is a recorded null (CEJA is a source-side phase-out, not an LSE share obligation). Qualifying sets are per-statute data resolved against `FUEL_TYPE_MAP` — nuclear IS admitted here (the separate row family CX-6a points to). Targets are ZERO before each statute's first knot (not edge-held). Each row carries its own feasibility escape (a hard 100%-by-2040 row is an infeasibility bomb). The clean dual enters the existing `max()` attribute doctrine at the capacity screens, fuel- and zone-resolved (`policy.clean_tiers`); a wind MWh satisfying both families is correct (two constraints, one MWh) with generator credit = `max()`, never a sum. ARMING IS BLOCKED pending the open §45U-vs-clean-dual composition for nuclear (§45U(b)(2)'s phase-down implies phase-down-then-add, not `max()`).

```
# NOx cap (same builder as the CO2 mass cap, nox_rate coefficient)
Σ_g Σ_t nox_rate[g] × P[g,t] ≤ nox_limit                              # annual
```

The CO2 mass cap above is the first realized constraint of this family; a NOx mass cap is the same `_build_mass_cap_rows` builder with `nox_rate` in place of `emission_rate` and is a trivial follow-on (out of the current scope). `policy/constraints.py::get_active_policy_constraints` is the wiring point that surfaces these specs to the dispatch builder.

**Energy Attribute Certificates (EACs) — exogenous attribute prices, adder-kind.** EAC is the umbrella term for the policy- or market-set clean-energy payment a resource earns per MWh, distinct from the energy price: RECs (wind/solar), nuclear ZECs, CCS clean-energy credits, offshore-wind ORECs, clean-firm geothermal credits, and storage-discharge incentives. The exogenous per-tech `eac_price_*` scalars (`ScenarioConfig`, Tier 1, all default 0.0 = byte-identical off) enter in exactly two places, adding **no LP rows** (`policy/eac.py`):

- **Dispatch (real bidding behavior):** each credited generator's marginal cost is *reduced* by its EAC once, pre-P0 (`apply_eac_to_mc` — nuclear, gas_cc_ccs, geothermal, offshore wind), and the wind/solar zonal dispatch adders and storage discharge credit take theirs via `compute_eac_dispatch_credits`. A production-type tax credit (wind PTC) **stacks** with the EAC in dispatch bids — both are real per-MWh revenue a curtailed MWh forgoes.
- **Capacity economics (the `max()` no-stack rule):** each MWh of clean generation mints ONE attribute certificate, sold once to whichever buyer clears higher. Attribute revenue in the retirement and new-entry screens is therefore `max(exogenous EAC, endogenous RPS shadow price, clean-tier dual where the family is armed) × MWh` — never a sum (`capacity.compute_attribute_revenue`; the RPS dual is credited only to RPS-eligible renewables, the clean-tier dual only to the row's statutory qualifying fuels in its eligible zones — `policy.clean_tiers.clean_credit_for_zone`). The IRA §45U existing-nuclear PTC supports retention through the same seam, folded in as a further `max()` (never stacked with a ZEC). The §45U-vs-clean-dual composition is OPEN and blocks the clean family's arming only (FFR-6B §6.4).

**Federal CES layer (national EAC premium, W2-A).** A national clean-energy standard is modeled as an exogenous federal certificate premium joining the same one-certificate `max()` family (`policy/federal_ces.py`; gate `federal_ces_enabled`, **forecast-only** — the backcast `__post_init__` guard makes it unusable as a backcast tuning channel, rule 13 `[R-MEASURED]`; default-off keeps dispatch bytes and cache keys identical):

- **Premium path (year-aware, real 2026$/MWh):** `premium_for_year` resolves sparse `{year: value}` knots (linear interpolation, edge-held — the `STATE_RPS_FLOORS` pattern) or `base × (1 + escalation_real)^(year − 2026)`. A flat real premium is CPI-tracking in nominal terms (owner default: escalation 0).
- **Crediting modes:** `clean_capture` (default) credits eligible zero-carbon fuels at 1.0, abated gas at the policy-assumed `federal_ces_ccs_capture_fraction` (0.95 — the owner's target capture rate; distinct from the engineering capture-rate fields), unabated fossil 0. `cesa_ci` credits eligible fuels `clip(1 − CI/0.82, 0, 1)` (Bingaman S.2146 benchmark) on each unit's own LP-boundary CO2 rate, extended to unabated gas CC at or under the 0.45 t/MWh eligibility cutoff (≈ EPA §111(b) new-CCGT NSPS; the fraction is always computed against the benchmark, never the cutoff).
- **Effective prices, all consumers:** every seam takes `max(legacy eac_price_*, premium × credit fraction)` — dispatch per-unit (`effective_unit_eac_prices` through `apply_eac_to_mc(mc, fleet, config, year)`), wind/solar/storage dispatch credits (storage only under `federal_ces_storage_eligible`, owner default off), the retirement screen per-unit (`effective_eac_price_for_unit` on the unit's own fuel + CI), and both new-entry screens per-tech (`effective_eac_price_for_tech` — this is what lets `nuclear_smr` and the hydrogen turbines earn the premium). The caller-side `max()` against the RPS dual and the §45U fold are unchanged. The **CCS-retrofit screen is deliberately not wired** — its economics are redesigned in W2-C (plan §11) and it keeps its legacy `eac_price_gas_cc_ccs` input until then.
- **State-RPS suppression counterfactual:** `federal_ces_replaces_state_rps` (with the master gate) skips the state RPS LP row entirely (`rps_target` stays `None`), so no REC dual exists and the federal premium is the only attribute mechanism — the pure-federal scenario for RPS ISOs (moot only in ERCOT, whose all-zero floors build no row; PJM carries a row since the FF-1E-policy refresh — stale-comment fix, FFR-6B §5.4).

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

The captured-CO2 disposal term is a constant $/MWh and folds into the unit's VOM; the residual-emissions term is ordinary `emission_rate × carbon_price`, so standard marginal-cost assembly reproduces the formula with no special-casing. CCUS becomes **more competitive as carbon prices rise** — the residual term shrinks relative to the full carbon cost an unabated plant pays — and the model finds the carbon-price crossover endogenously. The IRA §45Q credit ($85/tCO2 stored) enters the new-entry LCOE screen as a variable-cost offset and expires after `ira_ccus_45q_last_year` (default 2032). (The IRA expiry is **not** a single `ira_expiry_year` switch — it is split per credit: `ira_wind_solar_last_year` 2027; `ira_h2_45v_last_year` 2027; `ira_ccus_45q_last_year` 2032, gated at the project's **commit** year as a begin-construction-deadline proxy so an eligible project keeps its full credit window; and the "other clean" tech-neutral credit on a four-knot **step-down ladder** rather than a cliff — 100 % through `ira_other_clean_last_full_year` 2033, then `ira_other_clean_75pct_year` 2034, `ira_other_clean_50pct_year` 2035, and 0 % from `ira_other_clean_phaseout_end` 2036.)

#### 1.5.3 Enhanced Geothermal

Enhanced geothermal systems (`geothermal`, EGS) enter as zero-fuel dispatchable baseload generators with a high capacity factor (~90%). They are **not intermittent** — they do not follow wind/solar CF profiles. They can provide flexibility, turning down to a `pmin` of ~20% of rated capacity. A steep learning curve is assumed (analogous to early solar). Geothermal earns the same zero-emission production tax credit as wind.

#### 1.5.4 Offshore Wind

Offshore wind (`offshore_wind`) is a **separate renewable category** from onshore wind: higher and less variable capacity factors, higher costs, and distinct zone eligibility. By default it is a candidate only in CAISO (Pacific-coast floating); the Gulf-coast ERCOT potential is left as a future sensitivity. It is modeled as a **zero-marginal-cost `Generator`** (Option A), rather than as a new LP variable class — the LP dispatches it like any other generator and curtailment falls out of the capacity bound. This keeps the LP structure unchanged.

Offshore wind capacity factors are derived from the onshore wind profile for the same ISO by applying a physical smoothing window (default 6 hours, reflecting reduced ocean gustiness), a minimum CF floor (default 8%, reflecting persistent offshore resource), and rescaling to the target annual-average CF. This preserves the real temporal patterns (diurnal, synoptic, seasonal) from the EIA-930 data while producing a less variable, higher-average profile that matches offshore wind's physical characteristics. The derived profile is injected into the generator's hourly availability array, so dispatch varies realistically across hours.

#### 1.5.5 Additional Storage Durations

Three long-duration storage technologies — 12-hour lithium-ion, vanadium-redox flow batteries and adiabatic compressed-air — are added to the storage technology menu. They use the **same LP formulation** as the existing storage units (`power_cap`, `energy_cap`, `eta_chg`, `eta_dis`); only their economics differ, which drives different dispatch patterns.

### 1.6 Unit Commitment — LP Screen Heuristic (P0/P1 production; P2 archived)

Pure merit-order LP left fast-cycling units (notably ERCOT gas CT) badly under-dispatched, because a single LP solve has no notion of start-up cost or minimum run length. The model therefore carries a **commitment layer** (`model/commitment.py`). It stays **pure LP — there is no MIP and no binary variables**; commitment is a heuristic screen applied *between* LP solves by zeroing a unit's availability in hours it is decommitted, then re-solving. **Two passes are the production path — P0 and P1** (see below); a third, P2, is an archived opt-in artifact (`ScenarioConfig.commitment_enabled`, default `False`). The three passes, as built:

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

**P1-native commitment bridges (the production commitment-state mechanisms).** Three gated mechanisms inject a committed-state `min_gen` floor *before* the single scored P1 solve, detected from the model's own base-cost **P0** run pattern (`pipeline/commitment.py`, injected at the P0→P1 seam in `pipeline/solve.py::run_energy_solve`) — forward-derivable and condition-responsive by construction, no measured generation enters: **(a) the CAISO RA must-offer bridge** (`caiso_ra_mustoffer`, CAISO default-on — `caiso_ra_p1_floor_fleet`/`build_caiso_ra_p1_prep`, the midday-gap construction described under P2 above, now P1-native), and **(b) the ERCOT gas commitment bridge** (`ercot_gas_commitment_bridge`, default off, ERCOT-only — `ercot_gas_bridge_p1_floor_fleet`/`build_ercot_gas_bridge_p1_prep`): the same ISO-neutral detector (`model/commitment.py::caiso_ra_mustoffer_min_gen`) scoped to merchant gas-CC (`fuel_types=("gas_cc",)` — CT is physics-inert for the economic leg per the fast-start exclusion, ST_GAS is owned by its own drag mechanism), with `min_load_frac` = the measured ERCOT committed-CC LSL/HSL capacity-weighted p50 (0.574, 60-Day DAM disclosure 2023-2025, `ScenarioConfig.ercot_gas_bridge_min_load_frac`), the economic (≥ min-down) leg on the startup-restart inequality priced at the model's own P0 duals (`ercot_gas_bridge_startup`, default on with the gate) and bounded to one DA operating day (`ercot_gas_bridge_da_horizon`, default on — `DA_COMMITMENT_HORIZON_HOURS`). The CAISO startup-aware run screen is deliberately not exposed for the ERCOT bridge (dropped with cause — ERCOT-63, `docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §7). D-2 attribution ids: `ra_mustoffer_bridge` (7) and `gas_commitment_bridge` (17), each with a zero-forcing ablation entry and a cited D-4 window (`scripts/legitimacy_diagnostics.py`). The ERCOT bridge's hooks are built as a PAIR by `pipeline/commitment.py::build_ercot_gas_bridge_p1_preps` (the single-hook `build_ercot_gas_bridge_p1_prep` wrapper remains): when the companion gate `ercot_offer_surface_lowcurve_floorscoped` is on (ERCOT-64 — the measured committed-LSL bid applied via the `p1_bid_adjust_prep` seam ONLY in the bridge's own floored plant-hours; mutually exclusive with the tranche-wide `ercot_offer_surface_lowcurve` and hard-requiring the bridge, both fail loud), the bridge floor is computed ONCE per P0 result and shared by the fleet hook (the floor) and the bid hook (its hour mask), in both orchestrators. Probe verdict (ERCOT-64, 2026-07-13, diagnosis §8): the floor-scoped markdown is **provably inert** — the bridge floor clips at the committed tranche's own capacity on every bridged plant, so the tranche is exactly pinned in the markdown's whole window and its bid coefficient cannot move the LP solution or duals; both markdown variants stay default-off (the LSL price-side enumeration is closed; the committed-state inflexibility is carried by the bridge STATE alone). **(c) the NYISO gas commitment bridge** (`nyiso_gas_commitment_bridge`, default off, NYISO-only — `pipeline/commitment.py::build_nyiso_gas_bridge_p1_prep`): the same ISO-neutral detector run ONCE PER ELIGIBLE CLASS, because the two classes' measured minimum stable loads differ by more than 2x. Scope is the merchant slow-start gas fleet by unit PHYSICS (rule 18 `[R-PHYSICS]`), never a class-name tuple: on the NYISO keeper fleet `CC_REGULAR` resolves to min-down 4-8 h / $50 per MW and `ST_GAS` to 8-12 h / $35 per MW (both slow-start), while `CT_PEAKER`/`CT_CHP` resolve to 1 h min-down / $20 per MW and are therefore unreachable by both legs; the `*_CHP` groups are excluded by the detector regardless. `min_load_frac` is MEASURED per class from EPA CAMPD unit conduct (NYISO publishes no 60-Day-DAM equivalent, so the ERCOT LSL/HSL identification is reconstructed from the meter via the WP-3 loading-when-on construction: HSL = p99.5 of pooled load, LSL = p5 of online-hour load, class value = capacity-weighted p50 across units — `scripts/data/derive_campd_gas_commitment_params.py`): CC 0.523 (`nyiso_gas_bridge_cc_min_load_frac`), ST_GAS 0.239 (`nyiso_gas_bridge_st_min_load_frac`); the CC value lands within 9 % of ERCOT's independently published 0.574, which cross-validates the reconstruction. The economic leg (`nyiso_gas_bridge_startup`) and DA-horizon bound (`nyiso_gas_bridge_da_horizon`) mirror the ERCOT ones. It adds a THIRD leg the other two bridges do not have: the **minimum-run-duration extension** (`nyiso_gas_bridge_min_run`, the `min_run_hours` argument on the shared detector) — a detected P0 run shorter than the unit's minimum run is extended to it and the extension hours floored at minimum stable load, with the extended blocks then defining the run pattern the gap bridges scan, so an extension reaching the next run CLOSES that gap rather than it being bridged twice (rule 19 `[R-ONE-MECH]`). Min-run values come from the published class tables (`COMMITMENT_PARAMS_BY_FUEL`) unless `nyiso_gas_bridge_{cc,st}_min_run_hours` override, and a keeper override must be identified from the measured CAMPD run-length distribution in the same artifact. D-2 id `nyiso_gas_commitment_bridge` (20), with its own ablation entry and cited D-4 windows for both floored classes. It is the REPLACEMENT for NYISO's h14-21 peak-window reliability-floor limbs (owner directive 2026-07-27), so it is armed together with `iso_configs.NYISO_PEAK_WINDOW_FLOORS_OFF` applied through `reliability_floor_overrides` — substitution, never stacking (rule 19 `[R-ONE-MECH]`).

A gated ERCOT variant (`ercot_as_aware_commitment`, requires the multi-product AS co-optimization) makes the opt-in P2 pass **commitment-state-aware for reserves**: the screen values a unit's AS revenue (the model's own P1 reserve duals × headroom) alongside energy margin, an AS-adequacy floor re-commits cheapest units up to the measured AS requirement, and the P2 reserve headroom is re-scoped by the commitment state — a decommitted plant's econ **and peak** tranches leave the shared-headroom RHS (`couple_peak`), online CTs join the synchronized (fast) product pool per-hour via the P2 availability, and offline quick-start capacity backs Non-Spin only through a reserve-only extra-cap term (`reserve_config.ercot_commitment_headroom_overrides`). A second gated ERCOT flag (`ercot_ecrs_conservative_deployment`) represents the published pre-reform ECRS deployment design on the ECRS demand curve — a **P1-level** mechanism (it changes the LP's reserve demand, no commitment pass involved): no price-based release from ECRS go-live (2023-06-10) through 2024-07-31 (a single demand step at the offer cap), reverting to the standing VOLL-anchored ramp from 2024-08-01 (see `docs/parameter-citations.md`, "ercot_ecrs_release_reform_*"). Both are default-off structural mechanisms. Probe verdict (`2026-07-02-ercot27-ordc-structure`, 2026-07-03 calibration-log entry): the 2023 scarcity-month improvement comes entirely from the **P1-level** structure (ECRS withholding + AS carve-outs); the AS-aware **P2 pass added no scarcity-month signal and only a broad all-month price elevation** (the exact-coverage adequacy-floor artifact) — it is not part of any recommended configuration. Dashboard scoring note: the run explorer scores a bundle's **primary** dispatch pass — P1 for every normal (P1-only) bundle, byte-identical to before; a P2-scored registration can only exist for a run that explicitly opted into a commitment pass.

### 1.7 Outage & Availability Modelling — Forecast vs. Backcast

A unit's hourly `availability[g,t]` multiplies its `Pmax`. Two regimes:

**Forecast (statistical — the default).** Availability `= 1 − WEFOR(age) − DERATE(age) − POF(shoulder only)`, from the per-plant-group `THERMAL_AVAILABILITY` table (`config/constants.py`):
- **WEFOR** (forced-outage rate) is flat year-round and escalates with age past an onset year.
- **Planned outages (POF)** are distributed across the year by a **historically-derived monthly maintenance shape** (`MAINTENANCE_MONTHLY_SHAPE`, `config/constants.py`) — a per-plant-group 12-month weight learned from the measured timing of spring/autumn maintenance in the CAMPD unit-outage extracts (all six ISOs, pooled — a forecast shape, *not* pinned to any one backcast year). Each group's weights are the planned-maintenance excess over its annual-minimum (forced-outage-floor) month, normalized to a month-length-weighted mean of 1, so the per-hour planned-maintenance derate is `POF · (shoulder_hours/8760) · w[group][month]`. Because the shape has a month-weighted mean of 1, the group's **annual POF budget (`POF · shoulder_hours`) is conserved exactly** — only its seasonal *distribution* is sharpened from the legacy flat five-month block to the measured curve (peaks Apr and Oct–Nov, ≈0 at the Jul/Aug summer peak, modest in winter). Applies in **forecast** mode (`ScenarioConfig.maintenance_monthly_shape`, default on); set it `False` to restore the legacy flat block over `_CC_SHOULDER_MONTHS = {3,4,5,10,11}`. Independently, in the **summer peak** (`{6,7,8,9}`) only a fraction (`_SUMMER_WEFOR_SHARE = 0.30`) of the forced-outage rate applies, with the displaced WEFOR redistributed into the shoulder, so firm capacity is available for the load peak. Derivation/verify: `scripts/data/derive_maintenance_shape.py`.
- **Seasonal capacity derate** (ambient): gas turbines lose ~10–12.5% of capacity in summer.
- Nuclear uses a monthly capacity-factor shape (NRC PRIS refuelling pattern), refuelling concentrated in spring/autumn.

The monthly maintenance shape is forecast-mode shaping (responds to forecast conditions through each group's `POF` budget) and is **distinct from the backcast overlay below** — it never reads a specific year's outage windows, only the pooled seasonal *shape*. Backcast runs (`outage_source == "historic"`) keep their measured overlay and are unaffected by the flag.

**Backcast (historic overlay — calibration only).** When a backcast config sets `outage_source == "historic"`, `data/outages.py` overlays *actual* sustained outage windows (CAMPD-derived, coal/CC plants, ≥48 h CF<5% gaps) onto the model's fixed 8760-hour clock, plus a unit-level derate from the ERCOT unit-outage extract and CAMPD partial-outage (CF-ceiling) plateaus. The statistical POF for overlaid groups is dropped (`coal_drop_pof`) to avoid double-counting. The family carries three gated companions: short (1-5 day) baseload-coal windows (`unit_outage_short_windows`), unit-grain partial-derate plateaus (`unit_partial_outage_windows`), the declared-event-window revealed derates (`unit_outage_maxgen_events` — CAMPD per-unit derates inside the `maxgen-events` registry's declared capacity-emergency windows only, class-agnostic, under the frozen identification guards of `scripts/data/derive_campd_maxgen_outages.py`: $150 DA in-merit certificate region-scoped, ±45-day capability basis with best-event-hour credit, disjointness vs the std/short extracts; the only channel that can carry the measured CT/CC event-window leg — built miso-69, default off, in no keeper recipe). The same registry also drives a *price-formation* companion outside the availability family: declared-window ELMP emergency-tier pricing (`maxgen_emergency_tier_pricing` — inside a registry window declared at Max Gen Warning or higher, the declared region's physical zones reprice the load slack from the ISO bid cap to min(voll, tier floor): $500 Tier 1 at Warning/Step 1, $1,000 Tier 2 at Step 2+, the SOM-footnoted ELMP emergency-supply offer floors; `data/maxgen_events.py`, the RBDC/zonal-ORDC curves are never edited and off-window the slack cost equals voll by construction — built miso-70, default off, backcast-only). **Forecast runs never use this overlay** — it exists to reproduce a specific historical year for calibration, and degrades gracefully to the statistical model when the extract is absent.

**Regulatory availability overlay — NYSDEC 227-3 (NYISO, `nysdec_peaker_rule_availability`, default off).** The DEC "peaker rule" (6 NYCRR Subpart 227-3) caps ozone-season (May 1–Sep 30) NOx from simple-cycle turbines in two phases (2023-05-01 / 2025-05-01); units whose compliance plan is ozone-season shutdown or reliability-only operation are unavailable to the energy market inside the window. The curated unit-level schedule (`data/raw/reference/nysdec-227-3-peaker-compliance.csv`, extracted from the NYISO Gold Book Tables IV-3..IV-6 across the 2023/2024/2025 vintages with per-unit citations) zeroes/derates each restricted unit's availability inside its effective windows (`data/outages.py:nysdec_peaker_restrictions`). Availability **only**, never an offer/price change — the same admissibility class as the CAMPD outage windows (an exogenous regulatory event with a forward story: the schedule extends through the 2030 NYPA small-plant phase-out), and unlike the historic overlay it is *not* gated on `outage_source` (the regulation binds in any mode). Units the NYISO STAR process designated to remain in operation past the compliance date (the Gowanus 2&3 / Narrows 1&2 barges, to 2027-05-01) are carried in the CSV for the audit record but never restricted.

**Fast-start tranche pricing (`tranche_startup_amortization`, + measured-run v3 `tranche_startup_measured_runs`, both default off).** The ISO-NE Order-825 / NYISO GT-hybrid fast-start pricing analogue: the fast-start-capable gas tranches (CT_PEAKER/CT_CHP econ+peak; the CC duct/quick-response peak band) carry the bin's NREL start cost, which `model/commitment.py:compute_monthly_markup` amortizes into the P1 bid — the fuel-price-invariant commitment-cost component of the real offer stack. v2 amortizes over each tranche's own P0 run lengths, which is circular when the offer level itself is wrong (too-cheap offers → long P0 blocks → ≈0 markup → the lever self-disables; the nyiso-44 probe finding). v3 (`tranche_startup_measured_runs`) instead uses the unit's **CAMPD-measured median start-to-stop run length** (`scripts/data/derive_campd_ct_run_lengths.py` → `data/raw/_processed-legacy/campd_ct_run_lengths_<ISO>.csv`, pooled 2023–25, ISO-class fallback) as the amortization-horizon **ceiling**: `markup = startup / max(1, min(P0_month_avg_run, measured_median))`, a month with no P0 runs amortizing over the measured horizon outright — the ex-ante expected-run basis real GT offers form on, with the endogenous run only ever *shortening* the horizon. The measured run length is a rule-13 `[R-MEASURED]`-admissible measured market-behaviour parameter (same class as the CAMPD committed shares): it regenerates from the CAMPD pipeline for any vintage and re-derives only when its source data updates (rule 23 `[R-FROZEN-DERIVE]`). CC peak (duct) bands keep the v2 P0 basis — a duct burner's run is not a CEMS start-to-stop block.

> **Admissibility rule for measured data (CLAUDE.md Non-Negotiable Rule).** The outage overlay is the *canonical allowed* use of measured data: a unit outage is a **physical availability event** that enters as an input (`availability[g,t]`), is reproducible (the same window-detection logic runs on any year's CAMPD), and has a forward analogue (the roadmap statistical/historically-derived maintenance profile responds to forecast conditions). The discriminating test for any measured input is: *could the same quantity be produced for a forward year and respond to changed conditions?* Inputs that pass — outage windows, F923 delivered fuel prices, plant-specific CEMS emission rates, measured AS power reservations, temperature/net-load reliability-floor coefficients (§1.8) — are allowed even in backcast mode. **Forbidden** is feeding a measured *outcome* back to force the fit: pinning a unit to its observed CEMS generation (`ct_deployment_overlay`, `reliability_deployment_overlay`), an offset tuned to the price/volume residual (the former `ordc_reliability_deployment_mw`, **deleted outright 2026-07-04** per rule 26 `[R-DELETE]` — deprecated knobs that still parse are re-armable answer keys), or rescaling a potential so the model's *delivered* output lands on the actuals. Those have no forward analogue and are default-**off** diagnostic probes only — never keepers. The former per-plant EIA-923 must-run floor (`ct_mustrun_per_plant`) and CEMS deployment overlay (`ct_deployment_overlay`) are demoted to default-off diagnostic probes — they are measured-outcome floors with no forward analogue (the p97-CF ceiling used by the old reliability-floor mechanism is also removed). See `docs/backcast-measured-data-audit-2026-06.md` for the current compliance status.

### Calibration & Validation — cross-reference

This spec covers the LP formulation, commitment, and the forecast/backcast
outage-modelling split above; it does **not** cover how a backcast run is
scored, gated, or declared a keeper. For the calibration rubric (C1–C8),
holdout tiers (train/validation/locked-test), DOF ledgers and the
calibration-frontier designation, see
`docs/calibration-and-validation-methodology.md` — the authoritative
narrative reference, companion to `docs/calibration-determination-rubric.md`
(the criterion-by-criterion rubric spec) and the protective governance rules
`[R-FLOOR-WINDOW]` … `[R-DELETE]` (CLAUDE.md rules 17–26). The forecast
determination regime is `docs/forecast-determination-rubric.md`.

**The benchmark basis is delegated too.** How the backcast *actual* side is
constructed — the G-21 combined-fossil reconcile, the unit-class CAMPD backfill
bucketing, and the G-21b preliminary-vintage split anchor, all three the
unconditional go-forward default for every ISO since the owner directive of
2026-07-12 — is specified in full in the determination rubric **§0b**, including
the fallback path this spec never carried. It is scoring-side material and lives
there, not here. The one invariant worth restating because it constrains what
the model may be *compared against*: **no raw EIA-930 per-fuel cell ever gates a
scored class or family number** — EIA-930's BA-reported gas/coal attribution
mis-splits against CEMS by 7–21 TWh/yr, so it is trusted for the fossil *level*
only, never the *split*. Determination flips under this basis are honest and
stand; nothing may be tuned to un-flip them (rules 1 `[R-STRUCT]`,
13 `[R-MEASURED]`, 23 `[R-FROZEN-DERIVE]`).

### 1.8 Dispatch-Time Reliability Floor — Temperature / Net-Load Commitment

An energy-only LP decommits thermal generators whenever their marginal cost exceeds the clearing price, even in hours where a real system operator would hold them online for local reliability or ramping reserve against weather-driven load spikes. The **temperature/net-load reliability floor** (`transmission.inject_reliability_floor`) corrects this by raising `FleetArrays.min_gen` — the hourly lower bound on dispatched power — for thermal units whose real-world commitment is temperature- or net-load-driven. The mechanism is structural (mirrors how UC models commit-then-enforce-Pmin), forward-reproducible, and ISO-agnostic.

**Registry.** Each ISO's floor is a list of per-(zone, plant_class, driver) limbs in `RELIABILITY_FLOOR_REGISTRY` (`config/iso_configs.py`), seeded from `data/raw/reference/reliability_floor_coeffs_<ISO>.csv` — one row per limb. All six ISOs have derived coefficient CSVs (~221 total limbs; ~30 enabled, the rest shipped `enabled=False` because their temperature response is too weak to warrant a floor). `ReliabilityFloorSpec` is a frozen dataclass with fields: `zone`, `plant_class`, `driver` (`"tmax"` / `"tmin"` / `"netload"`), `threshold` (°C or GW), `floor_pct`, `enabled`, `min_event_hours` (24 for fast-start; 48 for steam), `distribution` (`"cheapest_first"` or `"pro_rata"`).

**Day gate (no hour-of-day windows).** On each calendar day:
- `driver="tmax"`: flag all 24h if `tmax_c > threshold`
- `driver="tmin"`: flag all 24h if `tmin_c < threshold`
- `driver="netload"`: flag all 24h if the day's system peak net-load (GW) > threshold (net-load = demand − VRE availability, computed from exogenous scenario drivers, not endogenous dispatch, to avoid circularity)

On flagged days, `frac = floor_pct`; on unflagged days, `frac = 0`. The full-day step gate replaces the earlier hour-of-day window model — a committed boiler physically runs the whole day, not a 6-hour afternoon window.

**floor_pct = commit_frac × min_stable_pct.** Two physical/structural halves: `commit_frac` is the share of the class's capacity online on flagged days (from CAMPD `grossLoad > 0` — a commitment count, not a CF ceiling); `min_stable_pct` is the physical min-stable level of the class (Pmin/Pmax, from bin tranche data / turbine specs). The result is a floor the LP must meet; dispatch above it is economic. The deprecated p97-CF ceiling is removed.

**Coefficient derivation.** Per-(zone, class) limb coefficients are regressed from CAMPD daily CF vs zone daily TMAX/TMIN (`scripts/data/derive_reliability_coeffs.py`). A limb is `enabled=True` only when the temperature response is real — Spearman ρ ≥ threshold (e.g. 0.3), sample size `n` ≥ 30 flagged days, and `floor_pct` meaningfully above the mild-day baseline. Coefficients are **never** tuned to the price/volume residual; floor_pct is **never** set to a measured CF ceiling so output matches actuals. The same coefficients regenerate for a forward year and respond to changed weather (rule 13 `[R-MEASURED]`; rule 1 `[R-STRUCT]` forbids tuning them to the residual).

**Steam-gas event bridging.** ST_GAS/ST_CHP limbs carry `min_event_hours=48` by default so an isolated flagged day bridges to adjacent flagged days — a committed boiler spans the whole multi-day heat-wave or cold-snap. `_bridge_flagged_runs()` merges isolated flagged runs separated by sub-event gaps. CT peakers keep single-day gates (`min_event_hours=24`).

**Distribution.** `"cheapest_first"` (default): `_distribute_group_floor()` sizes the hourly group target and fills it from cheapest units first (by heat rate). `"pro_rata"`: each in-scope unit is floored at `frac × its own available capacity`. Composed into `min_gen` via `np.maximum`.

**Config.** `ScenarioConfig.reliability_floor: bool` (master switch, default off). `ScenarioConfig.reliability_floor_overrides: dict` (per-limb overrides keyed `"<ZONE>:<CLASS>:<driver>"` → `{"enabled"?, "floor_pct"?, "threshold"?}`). `ScenarioConfig.class_commitment_overrides: dict` (per-ISO×class `min_run_hours`/`min_down_hours` for the P2 commitment screen). New ISOs/limbs require only a coefficient CSV row and a weather file — no code changes.

### 1.9 Modelling Commitments & Stated Limitations

Five commitments define the model's class. They are load-bearing methodology —
an audit-relevant statement of where this model sits relative to commercial
production-cost practice — not implementation preferences.

- **Pure LP. No MIP, no binary variables.** The commitment layer (§1.6) is a
  *heuristic screen between LP solves*, never a mixed-integer program.
  Fractional dispatch within a committed unit is accepted. This is the model's
  sharpest deliberate divergence from commercial UC practice, and it is what
  makes duals available everywhere (below).
- **Prices are LP duals.** Rule 4 `[R-DUALS]`. The dual on the zonal energy
  balance *is* the zonal price (§1.3); the dual on the RPS row is the REC price;
  the dual on a mass-cap row is the allowance price. There is no separate
  pricing model, and no post-hoc price construction anywhere in the production
  path.
- **Full 8760 hours, always.** Rule 8 `[R-8760]`. No representative days, no
  representative weeks, no clustering.
- **One pass per year in capacity evolution.** Rule 10 `[R-ONE-PASS]`. No
  within-year convergence iteration (§5.1).
- **The interface is CLI + YAML + Parquet.** The model has no service layer:
  no API server, no request/response boundary, no web framework in the solve
  path. `tools/launcher.py` is a local convenience UI — a stdlib
  `http.server` on port 8765 — that shells out to the same CLI a user would
  type; it is not a deployment surface and nothing in the model depends on it.

**Stated limitations**, each a known omission rather than an unexamined gap:

- **No inter-hour generator ramp-rate constraints.** Online/offline reserve
  *classes* and a co-optimized reserve requirement do exist (§1.6, §5.5), but
  true MW/min ramp limits between adjacent hours do not. Flagged as a future
  enhancement.
- **Perfect storage foresight.** The horizon is one LP, so storage sees the
  whole year's prices at once; the model is an upper bound on realized
  arbitrage. Bounded today by the `storage_daily_cycling` flag and analysed in
  full at §1.3.
- **No banking or borrowing across years** in the mass-cap family (§1.4): each
  year's cap binds independently, so the dual is an upper bound on a banked
  price in a tight year and ≈0 in a loose one.

Two items that were originally scoped out have since been built, and are
described in their own sections rather than as exceptions here: the unit
commitment layer (§1.6, still pure LP) and the backcast historic outage overlay
(§1.7, forecast runs never use it).

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

### 2.3 Construction Invariants

Five properties hold of the shipped builder. The first two are **binding
governance**, not implementation advice — they are CLAUDE.md non-negotiables and
a change that breaks either is a defect regardless of what it does to runtime.

1. **No Python loops over hours in LP construction** — rule 2 `[R-VECTOR]`. The
   builder assembles with `np.tile`, `np.repeat`, `scipy.sparse.kron` and
   `scipy.sparse.block_diag`. `for t in range(8760):` does not appear in the
   matrix builder.
2. **Struct-of-arrays before LP construction** — rule 6 `[R-SOA]`. Pydantic
   `Generator` objects are converted to `FleetArrays` (§3.1) — parallel numpy
   arrays — before the builder is entered. The builder's only inputs from the
   data layer are arrays and scalars; it touches no Python objects.
3. **The sparsity pattern is built once and the values filled separately.** The
   CSC column pointers and row indices are identical for every hour-block, so
   they are computed once and the `data` array filled by vectorized assignment.
4. **RHS assembly is vectorized too.** `Demand[z,t]` is a `(n_zones, T)` array;
   generator availability bounds are `pmax[:, None] * availability[:, :]`.
   These are numpy broadcasts.
5. **The CSC arrays are pre-allocated.** Nonzeros are counted analytically from
   the known structure, then `data` / `indices` / `indptr` are allocated once
   and filled.

Invariants 3–5 are why the memory envelope in §6.3 is dominated by the solver's
own working set rather than by construction churn.

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

**CAMPD per-plant binning (ERCOT default, `use_campd_bins=True`).** Documented in full in `docs/binning-methodology.md`. Built from EPA CAMPD gross generation (2023–24) cross-referenced with eGRID net generation and EIA-860 characteristics. Each plant gets **its own LP unit** (`data/raw/reference/custom-bin-assignments.csv`), classified into one of the dispatched groups — six gas classes (CC_CHP, CC_REGULAR, CT_CHP, CT_PEAKER, ST_GAS, ST_CHP) and the four coal subclasses (COAL_LIGNITE, COAL_PRB, COAL_BIT, COAL_WC; there is no bare COAL group — COAL-SUB, owner instruction 2026-09-25) — see `config/plant_taxonomy.py` — plus non-dispatchable OTHER. Every coal unit, in every ISO, carries its subclass from load (`data/coal.py::coal_subclass`: curated → EIA-923 receipts → EIA-860 retiree rank → partial-exit registry → the unit's own EIA-860 energy-source code; an unresolvable unit raises). Committed derived artifacts keep the coal fuel-family token `COAL` and are joined through `plant_taxonomy.artifact_class`, as are the mechanisms that aggregate across all coal (reliability-floor limbs, ERCOT class availability, online-capacity envelopes). Each bin is split into **tranches** that form a *rising offer curve* rather than a single flat marginal cost:

- **Must-Run (MR%)** — sunk-fuel coal floor or CHP behind-the-meter steam (the latter is removed from the LP and reconstructed post-dispatch by `compute_must_run_emissions()`). A covered CHP plant's BTM CO2 books at the same measured v2 rate as its grid tranches (not a separate heat-rate-derived number), and the forecast-mode BTM generation estimate uses `measured_class_cf()` — a gen-weighted op-hours utilization per CHP class keyed off the CEMS steam-load signature (`steam_load_klbh_sum > 0`) — in place of a flat assumed capacity factor, falling back to the flat `must_run_cf` (default 0.85) only when no measured class CF is available (EM-7 fix). The BTM *sizing share* itself is likewise measured: forecast years size `mr_mw` off the `chp-btm-share` datatype (`data.chp.measured_btm_share_by_plant`, `(EIA-923 net class gen − CAMPD grid-net gen) / EIA-923 net`, pooled across history) rather than the sector-keyed `chp_btm_pct` default, falling back to the bin's own MR% when a plant is uncovered; backcast years keep sizing from `chp_btm_pct` directly.
- **Committed (MC%)** — minimum stable load; the only tranche the commitment screen (§1.6) acts on. Bids cheap (`base_hr × offer["committed"]`, no `pmin`). For CC the committed share is derived **per-plant from CAMPD** (P5 of online CF) when `cc_committed_per_plant` is set — the ERCOT default — not from the flat CSV share.
- **Economic** — incremental in-merit dispatch, rendered **by default** as an `offer_curve_smoothing_n`-slice (default 6) rising heat-rate ramp anchored on the plant's own `base_hr`, *not* a single flat block. CC/coal fold the peak band into the ramp top.
- **Peaking (PEAK%)** — duct-firing / steep cost, `pmin=0`, never screened out; for CC/coal it is the top of the economic ramp rather than a standalone tranche.

No CC tranche carries a `pmin` floor and no bin-weighted heat rate is used — each plant dispatches on its own `Plant_Avg_HR_MMBtu_MWh`. See `docs/binning-methodology.md`.

Two further refinements wired into marginal-cost assembly:
- **Coal take-or-pay tranches** — three slices at different fuel passthroughs (e.g. VOM-only / partial / full fuel cost), so a coal unit's offer rises with quantity.
- **Coal passthrough sigmoids (per supply chain, per ISO)** — each coal supply chain (PRB rail take-or-pay, subbituminous, bituminous, mine-mouth lignite) discounts or marks up its bid as a smooth (sigmoid) function of the monthly gas price, with its **own independently tunable curve**: basin, rank, delivery mode and contract structure shift where the coal-vs-gas-CC crossover sits. Curves are **region-dependent** (`COAL_SIGMOID_DEFAULTS[(iso, supply)]`) — an (ISO, supply) pair with no characterized curve stays at flat passthrough rather than borrowing another region's economics. ERCOT PRB additionally has a tiered follower-curve variant for load-following plants.

**Gas-offer net-revenue margin form (`gas_offer_net_revenue_margin`, default off; design doc `docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md`).** The band-multiplier form above prices every gas band at `mult × base_hr × fuel(t)`, so the $/MWh markup over true marginal cost scales *linearly with the fuel bill* — unidentifiable against a fixed-margin offer inside a homogeneous training gas window, and rejected off-distribution by the NEISO 2022 validation rotation (the gas-marginal bulk over-prices at ~2.9× training gas while the fixed scarcity wall never forms the tail) and within-window by the winter-over/summer-under signature (neiso-45). When the flag is armed, each gas band whose curve declares a **measured physical basis** (`phys_*` keys on the `offer_curve_by_group` band — the ISO's own CAMPD marginal/average-HR artifact: block-average burn for the committed band, incremental burn for the econ ramp, physical duct/full-output ratio for the peak) is repriced to

`offer(t) = phys × base_hr × fuel(t) + max(0, mult − phys) × base_hr × P_anchor + VOM + emissions(t)`

— the physical burn keeps full delivered-fuel (and dual-fuel oil-parity) tracking, while the above-physical markup becomes a fuel-**invariant** $/MWh net-revenue margin (the missing-money / start-hurdle / competitive-reach component real bidders express in $ terms), identified at `P_anchor` = the training-window mean of the model's own delivered-gas series (`constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO`, `scripts/data/derive_gas_offer_margin_anchor.py`, rule-23 frozen). At `fuel = P_anchor` the reformed offer reduces **exactly** to the registered multiplier, so in-sample calibration is preserved at the identification point and `offer/mc` compresses toward 1 as gas rises. Implemented as a vectorized post-`assemble_mc` adjustment (`data/offer_curves.py::apply_gas_offer_margin`, `mc += markup_hr × (anchor − fuel)`) on the base cost, so P0 and P1 see the same offer curve; bands/ISOs without `phys_*` keys are byte-identical (neutral fallback, rule 25 `[R-ISO-SCOPE]`), coal keeps its own gas-keyed supply sigmoid (rule 19 `[R-ONE-MECH]`), and the `tranche_startup_amortization` fast-start adder remains its own registered mechanism (the band mults were calibrated with it on — no double count).

*Per-ISO identification (2026-07-23 rollout).* The mechanism is ISO-agnostic; each ISO supplies only its measured basis. **NEISO** ships it as a keeper (`2026-07-23-neiso-61-netrev-margin`); the physical `phys_*` keys and the delivered-gas anchor are now registered for **all six** ISOs. Each ISO's `phys_committed / phys_econ_low / phys_econ_high` are the cap-weighted p50s (`avg_committed_p50`, `marg_econ_low_p50`, `marg_econ_high_p50`) of its own `data/raw/reference/<iso>_campd_marginal_hr_summary.csv` (`scripts/data/derive_campd_marginal_hr.py --iso <ISO>`, rule-23 frozen — the same CEMS artifact the econ bands were grounded on); `phys_peak` is the **physical** bound — the 2.25 F-class duct-burner ratio for CC classes (registered peak ≥ 2.25 leaves the physical duct tranche fuel-scaled and turns the excess scarcity wall into a fixed margin, e.g. PJM CC_REGULAR 5.0 → +2.75), and the 1.0 full-output bound for CT/ST classes (so the $-denominated offer-cap wall above base burn becomes the scarcity margin). A registered bid below its measured basis clips to a zero markup (price-taker cogen/steam committed bands); a class with n ≤ 1 measured units is left neutral (no `phys_*` keys — NYISO CT_CHP, NEISO CT_CHP), as is any band without a declared basis. The per-ISO anchors (`GAS_OFFER_MARGIN_ANCHOR_BY_ISO`, each the 2023–2025 mean of that ISO's keeper delivered-gas overlay) are ERCOT 2.2494, PJM 3.3483, CAISO 4.7964, MISO 3.0492, NYISO 3.9046, NEISO 4.0763 $/MMBtu; the resulting CT_PEAKER scarcity margins ($113–298/MWh, cost-recovery 70–186 h/yr against `fixed_om_gas_ct`) sit inside each ISO's offer cap (the Potomac-SOM offer-side cross-check, `--net-revenue-check`). **ERCOT** is the sole ISO whose gas mults live in the shared base `offer_curve_by_group` (plus its recipe overrides and the `ercot_offer_surface_conditional` `peak_ladder` split); its `phys_*` keys are deep-merged from a phys-only `_ERCOT_OFFER_CURVE`, and because its peak carries the $5,000-ORDC 13.15× wall **and** the hour-triggered conditional surface, its margin-form composition must be verified by an A/B solve (tight vs loose hours) before it is judged a keeper.

**Per-plant offer curves.** By default the tranche shares and band heat-rate *multipliers* are per-*group* (`offer_curve_by_group`), but they are always applied to each plant's **own** `base_hr`, and the economic block is already a per-plant rising N-slice ramp (above) — so the default is plant-specific in level even where the curve *shape* is shared. An optional per-plant override sheet (`data/raw/reference/plant-tranche-config.csv`, `ScenarioConfig.plant_tranche_config_path`, off by default) additionally lets each listed plant carry its own **five-slice rising offer curve** — Must-Run / Committed / Econ-Low / Econ-High / Peaking shares plus per-slice heat-rate multipliers — bypassing the group shape too. This is the calibration lever for shaping an individual flagship plant's dispatch without disturbing its class total (`docs/binning-methodology.md`). A companion flag `cc_peaking_per_plant` moves the duct-burner peak band's CF onset for selected F-class CCs.

**Measured CT loaded heat rates (`measured_ct_heat_rates`, default off; `scripts/data/derive_campd_ct_heat_rates.py` → `data/raw/_processed-legacy/campd_ct_heat_rates_<ISO>.csv`).** Every band above is applied to the plant's `base_hr`, and for the non-ERCOT fleet that base is the **eGRID plant-average ANNUAL** heat rate. That figure is wrong for a peaker twice over: an annual average blends start, part-load and shutdown fuel into the number that sets an offer, and eGRID publishes **one rate per plant**, so at a mixed facility the turbines inherit the steam boilers' rate (E F Barrett 2511: FT4 twin-pacs and 188 MW boilers share 11.076; measured separately the turbines run 16.69). When the flag is armed, a `CT_PEAKER` generator at a covered plant takes its plant's **measured loaded** rate instead — per CAMPD unit, `heatInput / grossLoad` over hours at or above 80 % of that unit's own p95 gross load (≥ 50 qualifying hours, pooled 2023–2025, `unitType == "Combustion turbine"`), generation-weighted to the plant. The unit-level technology tag is what makes a mixed facility tractable: it contributes only its turbines rather than being dropped as unattributable. **Gross-to-net conversion is part of the measurement** — CAMPD meters gross load while eGRID, the LP's dispatched MW and the benchmark's actual are all net, so the rate is divided by the same committed parasitic factor the benchmark uses (`parasitic_load_factors.parquet`); skipping it overstates the correction by the station-service fraction (1 % for a bare CT, 10.2 % at Bayonne). Rates outside a physical simple-cycle band are flagged as meter defects and not applied; uncovered plants keep their eGRID rate. Applied per generator by class in `fleet/eia860.py::_rows_to_generators`, so only a mixed plant's turbines are repriced. Rule 13 `[R-MEASURED]` admissible (a machine's loaded heat rate regenerates for a forward year and responds to retrofits), rule 23 `[R-FROZEN-DERIVE]` frozen (re-derives only on a CAMPD vintage change). See `docs/FINDING-nyiso89-ct-heat-rate-2026-07-27.md`.

When a bin maps to a single physical plant, its CO2/NOx can be overridden with **CAMPD CEMS plant-specific emission rates** instead of the fuel-class default. The CO2 rate is booked at the plant's **physical** heat rate, never the bid-tranche heat rate — the offer-curve pricing multipliers (peak ×2.0–2.5, committed ×0.92) shape the bid stack, not the plant's CO2/MWh (R2/EM-4 fix, `data/fleet/assembly.py::bins_to_fleet`).

**Forward-mode source (v2, `use_plant_emission_rates_v2`, default **on**; `docs/handoffs/emissions-co2-rate-plan-2026-07.md`).** The per-plant CO2 rate is **mode-aware**: a **backcast** year books the target year's own measured CEMS rate (a reproducible physical input); a **forecast** year books the estimator base — the gen-weighted trailing average of the unit's multi-year CAMPD history, aggregated over only the CEMS units present in the target year's fleet (the unit-composition mask). This is wired end-to-end via `data/fleet/campd_bins.py::apply_plant_emission_rates_v2` → `data/emission_rates.py::measured_plant_rates`. The forward rate is *derived from* forward drivers and responds to changed operation (a retired unit drops out of the plant's composition mask), so it is rule-13-admissible in forecast — not the forbidden same-year pin. Rates are matched to each dispatch bin by `(plant_code, coarse fuel class)`, so a coal+gas facility (W A Parish 3470) gets **separate coal and gas rates** rather than the blended facility value — replacing the old `mixed`-plant exclusion.

`emission_rates.py::forward_plant_co2_rate` is the full four-piece estimator design (gen-weighted base + envelope-gated nearest-neighbor conditioning on simulated operation + the unit-composition mask + a class-distribution fallback, `class_median_rates`) and is certified by the leave-one-year-out harness `scripts/loyo_co2_rates.py` — never by a keeper's backcast fit. **Only the base + mask pieces are wired into the production dispatch path today** (`measured_plant_rates`, above); the envelope-gated NN conditioning and the class-median fallback are implemented and unit-tested (`tests/unit/data/test_emission_rates.py`) but are called only from the LOYO harness and its tests, not from `data/fleet/`/`runner.py`. Concretely: CEMS-uncovered plants still fall back to the generic `get_emission_rate(fuel, base_hr)` heat-rate default, and new entrants still take the static per-vintage `constants.CO2_RATES[tech][bin]` table — neither consults `class_median_rates`. The NN conditioning ships gated off (`constants.CO2_RATE_CONDITIONING_ENABLED = False`): the 7-year held-in LOYO (2018–2021 + 2023–2025, run 2026-07-05; plan §9.5) rendered the verdict — the envelope-gated sim-conditioned estimator never beat plain `a_gw` at any swept gate on ERCOT, the only ISO with persisted simulated operation — so the shipped estimator is the pure gen-weighted trailing average. The same sweep set the trailing window to the **most recent 2 years** of available history (`constants.CO2_RATE_TRAILING_WINDOW_YEARS = 2`): in the forward-chained direction (targets predicted from strictly-prior years, matching production use) the 2-year window won every per-target comparison on both ERCOT and PJM — measured plant rates drift with age/retrofits, so recent years are more predictive. Both constants are frozen against backcast residuals and re-derive only on a CAMPD data update (rule 23 `[R-FROZEN-DERIVE]`). Closing the class-fallback gap is tracked as a follow-on, not yet scheduled to a wave.

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
    iso: str = "ERCOT"              # any of the seven registered ISOs:
                                    # ERCOT | CAISO | PJM | MISO | NYISO |
                                    # NEISO | SPP
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
        """Deterministic hash of the resolved config. Used for result caching."""
        ...
```

**The cache key is a frozen surface, and it is not a naive hash of the
dataclass.** The shipped construction has two properties the sketch above does
not:

- **Drop-at-default over registered optional fields.** A field listed in
  `_CACHE_KEY_OPTIONAL_FIELDS` is dropped from the hashed payload when its value
  equals `getattr(ScenarioConfig(), name)` — the **live** default, recomputed on
  every call, not a frozen sentinel. This is what lets a new gated mechanism ship
  without invalidating every existing cached bundle. It has a consequence worth
  stating plainly: **flipping such a field's default does not move the key**,
  because the new value is then the live default and is dropped. A pre-flip and a
  post-flip config hash identically, and only the run ledger can see the
  difference. The inverse is useful — an *explicit* value that is no longer the
  default becomes non-default and hashes distinctly, so A/B control arms separate
  cleanly.
- **A registration ledger, CI-enforced.** Every optional field must be
  registered with its declared default, and
  `scripts/check_cache_key_registration.py` fails CI if a registered field does
  not resolve or if a declared default has drifted from HEAD. It also reports the
  live counts (fields, registered, resolving) — read them from the script, not
  from this document.

Because keys are the identity of every cached result, **a key move is a declared
epoch**, not an incident: the run that moves it records the invalidated
population and the purge instruction (the FFR-9C precedent, and the epoch pins
carried in `results/cache.py`). Byte-stability of the key is what makes the
byte-identity contract of §6.5 checkable at all. A YAML round-trip must hash to
the same key as the config that wrote it — the tuple/list coercion repair landed
in the 2026-08 debug sweep precisely because a byte-faithful reload once did not.

### 4.2 Single-Run Mode

CLI accepts a YAML file that overrides any parameter:

```bash
python -m market_sim run --config my_scenario.yaml
```

**Solve-window cap.** (The forecast program's §2.1b full-solve authorization
gate — `docs/forecast-development-plan-2026-07.md`.) Every `market-sim` subcommand — `run`, `sweep`,
`ensemble`, `matrix` — **refuses** a window spanning more than
`MAX_UNAUTHORIZED_SOLVE_YEARS = 5` solve-years unless `--full-solve-authorized`
is passed (`config/schedulable.py::assert_schedulable`, attached to all four
subparsers by `runner.py`). The refusal is a `SystemExit`, not a warning. T1
ladders (e.g. T1-H 2021–2025) fit inside the cap; T2/T3, golden-fixture, PB-5 and
W4-campaign windows are deliberately deferred until the owner authorizes them,
and the flag is the record of that authorization. Backcast configs are exempt —
their year span is governed by rule 22 `[R-HOLDOUT]` and its tier markers
instead, enforced separately by `scripts/run_calibration_full.py` and the CI
quarantine gates. See §5.1's year loop.

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
# sweep_demand_storage.yaml
sweep:
  demand_growth_rate: [0.005, 0.015, 0.03]
  storage_deployment: [low, mid, high]
# 9 more scenarios, orthogonal to the gas×carbon sweep.
```

(This example read `renewable_buildout_pace: [slow, mid, aggressive]` until
2026-09-01. That field was consumed by no model code — it produced nine
distinct cache keys over three distinct scenarios — and was deleted under rule
26 `[R-DELETE]`; the illustration now uses a field that actually reaches the
model. VRE buildout pace is governed by `entry_rate_limits`, not by a scenario
ladder. See `docs/handoffs/FINDING-capx-t16-driver-2026-09-01.md`.)

Sweeps can be composed (run multiple sweep files) or run independently. The runner deduplicates by cache key — if a scenario exists from a previous sweep, it’s skipped.

**No full factorial on all dimensions.** The user pairs parameters deliberately.

**Two expansion modes, and they are mutually exclusive.** `SweepDefinition`
(`config/sweeps.py`) gates purely on which of its two mappings is non-empty;
setting both raises. Both expand *onto* an optional `base_config`, so one engine
serves the sweep CLI (no base) and the matrix CLI (explicit `--config` base).

- **`sweep:`** — the cartesian mode illustrated above. A `{field: [values]}`
  mapping expands to every combination.
- **`cases:`** — the named-case mode. A `{case_name: {field: value}}` mapping
  expands to exactly one config per named case, and — unlike `sweep:` — the case
  **identity is preserved** through `case_configs`, so downstream output can
  label each member. This is the mode the shipped 13-case AEO/IPM-style
  scenario matrix uses: `configs/scenario_matrix.yaml`, run through the
  **`matrix` subcommand** (`python -m market_sim matrix --config <base> --matrix
  configs/scenario_matrix.yaml`), whose whole point is the labelled trajectory
  table a bare sweep cannot produce.

> **`SweepDefinition.mode` is a dead field.** The dataclass declares
> `mode: str = "factorial"`, and a shipped matrix file carries a `mode: cases`
> line, but **nothing in the model ever reads it** — expansion gates only on
> which mapping is non-empty. `mode: lhs` (Latin hypercube) and `mode: list` do
> not exist and never did; earlier revisions of this spec described them as
> supported and as "future", which was wrong in both directions. The field's only
> read site anywhere is a unit test asserting its default. Whether to remove it
> under rule 26 `[R-DELETE]` — a parameter that still parses but selects nothing
> is exactly the re-armable surface that rule addresses — is an open owner
> question, recorded here rather than decided.

### 4.4 Caching

Each scenario-year result is stored as a **single Parquet file**:

```
results/
  {iso}/
    {cache_key}/
      year_2026.parquet
      year_2026_p1.parquet   # Pass-1 dataset, written only when a
      year_2027.parquet      #   commitment pass runs (see below)
      ...
      year_2050.parquet
      config.yaml            # full resolved ScenarioConfig for reproducibility
```

Before running a scenario-year, check if the parquet exists. If yes, skip. This makes the system stop/resume capable and avoids recomputing validated results.

The Parquet contains all hourly outputs for that ISO-year: dispatch by unit, zonal prices, emissions, storage SOC, curtailment, flows, slack. Schema is fixed and documented in a data dictionary.

**Solve-pass tag.** `cache.get_cache_path(iso, cache_key, year, pass_label)`
appends `_{pass_label}` to the filename. `pass_label=None` — the default and the
only file a P1-only run writes — is the final-result `year_{year}.parquet`;
`pass_label="p1"` is the retained Pass-1 dataset `year_{year}_p1.parquet`,
written when a commitment pass runs so the pre-commitment solve stays inspectable
beside the final one. `is_cached` and `load_result` take the same tag, so a
pass-tagged file participates in check-before-run caching exactly like the
untagged one.

**The whole tree is relocatable.** `config/paths.py` resolves
`DATA_ROOT = Path(os.environ.get("MARKET_SIM_DATA_ROOT", REPO_ROOT))`, and both
`data/` and `results/` hang off it. With the variable unset this is exactly the
repo root, so the layout above is the default; setting it moves inputs and
cached results wholesale onto another volume without touching any config. Every
on-disk path in the model resolves through this module — never through
`Path(__file__).parents[...]`.

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
       §7), forecast-mode only. The INSTRUMENT-BOUND exogenous fossil exit
       channel (the only one until owner ruling Q30 armed limb 1b below).
    1. Apply ANNOUNCED retirements (EIA-860 planned date). NON-FOSSIL
       (nuclear/hydro/renewables/storage) honored only within the EIA-860 data
       horizon, beyond it only if the unit is in the confirmed registry
       (`NONFOSSIL_ANNOUNCED_HORIZON_YEARS`)
   1b. Apply the OWNER-FILED FOSSIL dates (EIA-860 Schedule-3 planned
       retirement year/month) as an exogenous input on step 0's own
       matcher/derate machinery — vintage-gated, reversal registry armed.
       GATED `fossil_announced_exits_enabled`, DEFAULT ON since 2026-09-02
       (owner ruling Q30 on the capx D42 A/B), forecast-mode only. A plant
       carrying a pending filed date is EXEMPT from the step-3 economic
       screen, which therefore decides the residual UNDATED fossil fleet
       (`forecast_fossil_retirement_economic` governs only what this limb does
       not reach)
    2. Apply CCS retrofit screen to existing gas-CC units (§5.6) — BEFORE the
       economic retirement screen, forming the joint retrofit-or-retire choice
       with step 3 (W2-C, national-ces plan §11): a gas-CC whose retrofit
       continuation beats staying unabated and clears its §45Q-windowed payback
       converts here instead of being offered only the exit
    3. Apply economic retirement screen (fuel-type-aware, uses Year N-1 results;
       includes the accredited reliability floor; units retrofitted in step 2
       are exempt this year — their loss counters restart as gas_cc_ccs)
    4. Apply known additions (EIA-860 under construction, signed PPAs)
    5. Apply economic new entry screen (LCOE vs expected revenue, including
       the prior year's REC price as clean-energy revenue)
    6. Apply reserve-margin adequacy backstop: force-build firm capacity if the
       economic screen left the system below its planning reserve margin.
       GATED `reserve_margin_build_enabled`, a TRI-STATE field defaulting to
       `None` = resolve per market design (G-41): ON for the ISOs whose design
       procures capacity to an adequacy requirement (PJM/MISO/NYISO/NEISO/CAISO),
       OFF for energy-only ERCOT and any ISO absent from `MARKET_DESIGN`. An
       explicit True/False overrides verbatim
    7. Assemble updated fleet → run dispatch LP (with RPS constraint) → cache results
```

The forecast horizon this loop may span is capped by the §2.1b authorization gate (§4.2): more than five
solve-years needs `--full-solve-authorized` on any `market-sim` subcommand
(§4.2). Backcast year spans are governed instead by rule 22 `[R-HOLDOUT]`.

The capacity-evolution mechanisms are steps 0–6. The RPS is no longer a force-build step: it is enforced as an LP constraint in the dispatch (step 7), and its shadow price feeds back into the economic new-entry screen the following year.

**Step order note (W2-C, 2026-07-17).** The CCS retrofit screen moved from after known additions to BEFORE the economic retirement screen — steps 2 and 3 are now the joint three-way evaluation (stay unabated / retrofit / retire) for retrofit-eligible gas-CCs, still one pass (rule 10 `[R-ONE-PASS]` — ordering, not iteration). Under the old order a loss-making CCGT exited at the retirement step without ever being offered the retrofit; now the retrofit screen values both continuations first, so a unit retires only when both fail. Cap-displaced retrofit candidates (the 3 GW/yr/ISO throughput cap) fall back to the unabated path and the normal loss-year counter — they are re-screened every year and may exit later if unabated keeps failing while the cap keeps binding. Retrofits still precede economic new entry, so a retrofitted CC displaces new-build CCS demand.

**Confirmed vs announced retirements.** Only *confirmed* exits — units bound by an enforceable public instrument (RTO deactivation acceptance, consent decree, statute, PUC/regulatory order, RMR end date) — are exogenous. They come from the hand-curated `confirmed-retirements` registry (one row per binding instrument, forward-reproducible per rule 13 `[R-MEASURED]`; superseded rows carry a cited counter-instrument and revert to the economic screen), read forecast-forward by `data.confirmed_retirements.load_confirmed_exits` and applied at step 0 (`apply_confirmed_exits`), which force-retires a unit-grain unit or derates a plant-binned tranche by the exiting unit's MW, bypassing the reliability floor. This is the **instrument-bound** exogenous fossil exit channel.

***Announced* fossil dates are ALSO exogenous, as limb 1b (owner ruling Q30, 2026-09-02; `fossil_announced_exits_enabled`, DEFAULT ON — capx D42/D44).** A fossil unit's owner-filed EIA-860 Schedule-3 planned retirement year/month is honored as an exogenous step-1 input: the rows are loaded by `data.announced_retirements.load_announced_fossil_exits` from the run's **ACTIVE EIA-860 vintage** and consumed through step 0's own matcher/derate machinery (unit-grain rows drop the unit, plant-binned rows derate the plant's tranches, first-half months carry a completion leg), so they bypass the reliability floor exactly as a confirmed row does. **Rule 13 `[R-MEASURED]` admissibility — the vintage gate:** a date is admissible in year Y only because it was on file at the run's information cutoff, the same gate step 0 applies to `instrument_date`, and the identical construction regenerates for a forward year from the then-current 860 — the additions pipeline already reads the same form's proposed-generator schedule as a forward input. The filed date is an ex-ante owner **plan** that responds to conditions (it moved for Baldwin, Sherco 1, Schahfer), never a measured outcome. The **reversal registry** is armed (a plant countered by a later public instrument — e.g. J H Campbell under DOE FPA §202(c) — is dropped), and under `hindcast_verified_announced_exits` each vintage row is additionally checked against the later in-repo vintages: a re-filed later date (a filed deferral) or a dropped date (a withdrawn plan) is honored per unit as the later vintage's information. The verification may **defer or cancel** a vintage exit, **never inject or advance one**. Zero free parameters, no fitted filter — an undated deferral is a false positive at full magnitude. **Rule 19 `[R-ONE-MECH]` reconciliation:** (a) a plant carrying a pending admissible date is EXOGENOUS to the economic screen (`dated_plant_unit_ids` → `exempt_unit_ids`) — the owner's filed plan *is* the exit decision for that plant, so the screen decides only undated plants and no unit's exit is decided twice; (b) the R-NEW admission cap's counterfactual fleet nets every dated exit due by the cap horizon, so the reliability floor's retention pool can neither retain a dated unit nor over-admit undated candidates against capacity that is leaving anyway; (c) the realized-year floor tests the post-step-1 fleet.

The superseded posture, and why it was ruled wrong: a coal/gas/oil unit's announced date used to be treated as an announcement, not a certainty, so for the whole fossil fleet step 1 was a default no-op and the economic screen alone governed the phaseout. Q30 ruled that rationale a statement about **precision**, not about admissibility — and D42 measured the precision: honoring the filed dates takes MISO's T1-H unit recall **5/19 → 16/19**, opens every non-coal exit class the reliability floor had held at exactly 0.0 GW, keeps `false_retire` at 0.0, reaches 98.5 % plant-grain precision of released MW under verification, and **displaces no economic-screen decision at all** (zero economic exits in every year). What it does not close: the **undated cohort** (real exits with no vintage date, unreachable by any date channel ex ante), the December-dated **majority-of-year roll** into the following year, and genuine deferrals. `forecast_fossil_retirement_economic` (default True) still governs everything limb 1b does not reach, so the forecast stays condition-responsive there (an undated fossil unit may exit early on losses or run on if it stays in-merit). Evidence and per-unit deferral counters: `docs/handoffs/FINDING-capx-d42-fossil-dates-ab-2026-09-02.md`; execution record `docs/handoffs/FINDING-capx-d44-fossil-dates-arm-2026-09-03.md`.

Non-fossil announced dates (nuclear/hydro/renewables/storage — policy/contract/end-of-life exits) stay deterministic only within the EIA-860 data horizon (`EIA860_OPERABLE_VINTAGE + NONFOSSIL_ANNOUNCED_HORIZON_YEARS`, default 5); beyond the horizon a non-fossil date is honored only if the unit is in the confirmed registry, so speculative 2040-2072 relicense/EOL placeholders stop force-retiring (the horizon gate activates with the confirmed channel; off = honor all non-fossil dates). The splits are the `fossil_announced_exits_enabled`, `forecast_fossil_retirement_economic` and `confirmed_exits_enabled` flags. After the data horizon (~2030) — i.e. once the filed dates and the confirmed registry are exhausted — the model is fully economics-driven.

### 5.2 Economic Retirement

The **screen** is one bar, identical under both rules: a unit fails the year when
its **net revenue < going-forward cost**. What differs is how a failing screen
becomes a realized exit, and that is selected by **`ScenarioConfig.retirement_rule`**
(`"pipeline"` — the default — or `"legacy"`;
`capacity_evolution/retirements.py::apply_economic_retirements`).

**The pipeline rule (`retirement_rule="pipeline"`, THE DEFAULT).** The R-NEW
decision/execution split (FF-0C §3.6, owner decision D1 = Option B 2026-07-17;
default flipped `"legacy"` → `"pipeline"` by owner decision **D-1, signed
2026-08-02**, `docs/handoffs/ffr-owner-sitting-2026-08-02.md` Addendum C.1). It
separates the *decision* to exit from the *execution* of the exit, with **zero
newly tuned parameters**:

1. **Uniform decision.** A unit whose attainable margin fails the identical bar
   at ONE annual screen becomes DECIDED. There is no per-fuel decision
   threshold — decision persistence is 0, the flat-expectation degenerate NPV
   form, an open DOF held by parsimony.
2. **Joint pipeline-entry competition.** All newly failing units across ALL
   fuels compete in the same year, worst-first by margin depth ($/kW-yr
   shortfall). Admission is capped by the existing accredited-adequacy
   requirement evaluated on the *schedule* of pending exits, tested at the
   schedule's **execution horizon** rather than the decision year. This removes
   the legacy rule's cross-fuel race and its fuel-partitioned eligible set.
3. **Soft latch.** A pipelined unit is re-screened annually and leaves the
   pipeline only by re-clearing the same bar (genuine economic recovery). One
   good year no longer erases the distress history.
4. **Execution after the identified lag.** A unit still pipelined at
   `decided_year + L_f` deactivates then, where `L_f` is
   `retirement_execution_lag_*` — the **measured EIA-860
   announced-to-deactivation medians** (RC-0B §a.3): coal 3, gas_ct 2, gas_cc 1,
   gas_st 1, oil 1, nuclear 3 years (`gas_cc_ccs` is `None` and inherits the
   gas_cc lag). The unit **dispatches normally until then**, as real
   announced-but-operating units do. This is where the per-fuel physics lives
   under the default rule.
5. **Reliability floor at execution, unchanged.** A floor-retained due unit
   stays online AND stays pipelined; execution is deferred and re-latched next
   year.
6. **Ledger attribution.** `event_sink["pipeline_events"]` records
   decided / re_confirmed / reversed / entry_capped / executed rows with years,
   so recall and false-retire scoring see the decision and the execution
   separately. Diagnostic only — rows record the decision, never shape it.

Queue **latency** (the execution lag) and queue **throughput** are two distinct
mechanisms for rule 19 `[R-ONE-MECH]` purposes (owner decision D-8, signed
2026-08-03): a constant per-fuel lag is a rigid time-shift operator, so latency
alone leaves exit-wave width invariant at exactly one year however many units
fail. The throughput half is `ScenarioConfig.exit_rate_limits` (default off),
which processes due exits strict-FIFO oldest-decision-first up to an MW cap.

**The legacy rule (`retirement_rule="legacy"`, non-default).** A year in which
`net_revenue < going_forward_cost` increments the unit's consecutive-loss
counter; a profitable year resets it to zero; the unit retires once the counter
reaches its per-fuel `retirement_years_*` threshold. **These per-fuel
consecutive-loss thresholds apply to this rule ONLY** — under the pipeline rule
they are unused. As-built defaults:

- **Coal:** 3 consecutive loss years. Identified (rule 23 `[R-FROZEN-DERIVE]` —
  re-derives only when the EIA-860 vintages update, never against a residual) to
  the measured EIA-860 announced-to-deactivation lag for coal: capacity-weighted
  / ≥300 MW median = 3 yr, left-censored over 66 % of announced coal MW, so a
  conservative floor on the announcement→deactivation pipeline. The threshold
  carries the full decision + lead-time total, so the same physical queue is not
  counted twice (rule 19 `[R-ONE-MECH]`). Owner-adopted 2026-07-16.
- **Gas CT:** 2 consecutive loss years. **Gas CC:** 3 (most patient — higher
  capital sunk, longer expected life). **Gas ST / oil:** 2. **Nuclear:** 3
  (irreversible exit). **`gas_cc_ccs`:** 3, like a modern CC.

The legacy counter is the configuration measured to eliminate PJM's coal wave
(recall 76 % → 0) and to false-retire 8.6 GW of MISO gas_st, and the third-party
peer review places it outside commercial practice entirely (no analogue in
IPM / ReEDS / PLEXOS-LT) — which is why the default moved. It is retained as a
selectable rule so every run committed before the flip stays reproducible
byte-for-byte.

Revenue and cost definitions (identical under both rules):

- Net revenue = the **attainable (pro-forma) inframarginal margin** `Σ_t max(0, price[z,t] − mc[g,t], r[g,t]) × pmax[g] × availability[g,t]` plus attribute payments (`max(effective EAC, prior-year RPS/REC shadow price) × annual_gen`, where the effective EAC is the unit-level `max(legacy eac_price_*, federal CES premium × unit credit fraction)` resolved for the screen year — `policy/federal_ces.effective_eac_price_for_unit`, §1.4; under `cesa_ci` a credited unabated gas CC earns its fraction on its own CO2 rate here, and the IRA §45U nuclear credit folds in as a further `max()`) and any capacity-market revenue, evaluated against the prior year's capacity-screen price signal. This is the unit's optimal per-hour response to the screen's own signal — the same price-duration pro-forma the Potomac SOM net-revenue tables are built from and the same basis the new-entry screen uses — **not** the prior LP's realized dispatch: the post-solve ORDC scarcity adder lifts the screen's prices in hours the pre-adder LP left an out-of-merit peaker idle, so a realized-dispatch margin structurally misses exactly the scarcity rent a peaker lives on (capacity-economics plan 2026-07 §5 step 2). `r[g,t]` is the hourly reserve-price signal (below); `mc` is the unit's *full* variable cost (fuel + VOM + emission prices) — not its bid: take-or-pay coal bids below fuel cost in dispatch because the fuel is sunk within the contract year, but on a retirement horizon the contract lapses, so fuel is avoidable and counts against the margin. (Two earlier formulations are superseded: *gross* energy revenue vs fixed cost let units "cover" FOM with money already spent on fuel; realized-dispatch margin under-collected scarcity ~40× on the SOM CT observable.) A profitable year resets the unit's consecutive-loss counter to zero.
- Reserve/AS valuation (`screen_reserve_value_enabled`, default on): each reserve-eligible unit's hourly value is its **best use** — energy margin or the reserve price, never both on the same MW (the co-optimization arbitrage condition). The signal is the reserve co-opt's own duals under `ercot_thermal_as_endogenous` (all-products tier for synchronized units, Non-Spin tier for offline-capable quick-starts, mirroring the co-opt's headroom cascade), else the post-solve ORDC scarcity adder — ERCOT pays real-time on-line/off-line reserves the same ORDC price the energy adder carries (RTORPA/RTOFFPA, Nodal Protocols §6.5.7.5). When the hourly signal is present it is the SOLE thermal AS pricing (rule 19 `[R-ONE-MECH]`); otherwise the screens fall back to the annual endogenous per-fuel rate or the calibrated exogenous flat rate, as before. Zero fitted parameters; the SOM CT/CC net-revenue tables are the external validity check, never a target.
- Going-forward cost = fixed O&M × FOM multiplier (not capital — sunk cost)
- FOM multipliers: coal = 1.3× (captures regulatory risk, carbon liability, ESG pressure), gas = 1.0×
- Retirement ordering: within each fuel class, least efficient (highest heat rate) retires first

These thresholds and multipliers are no longer hardcoded — they are `ScenarioConfig` fields (`retirement_years_{coal,gas_ct,gas_cc}` = 3/2/3 under the legacy rule, `retirement_execution_lag_{coal,gas_ct,gas_cc}` = 3/2/1 under the pipeline rule, `retirement_fom_multiplier_{coal,gas_ct,gas_cc}` = 1.3/1.0/1.0 under both), so retirement aggressiveness is a Tier-1 sensitivity lever. The values above are the as-built defaults, re-derived from `ScenarioConfig()` at each finalization pass rather than transcribed. (`retirement_reserve_margin` was DELETED with the floor-accreditation rebuild — the floor and the build backstop now share `PLANNING_RESERVE_MARGIN_BY_ISO`. `staged_oversupply_thinning` / `staged_thinning_max_gw_per_year` were likewise deleted, not zeroed, at the FF-1A flip — rule 26 `[R-DELETE]`; the throughput half they modelled returned as the externally-identified, default-off `exit_rate_limits`.)

**Reliability floor (accredited basis):** the surviving fleet's `accredited_firm_capacity_mw` (thermal at its ISO's published basis via `thermal_accreditation_fraction` — UCAP = 1 − EFORd, PJM's ELCC class rating, or ERCOT's seasonal rating; wind/solar pools at their **penetration-indexed published ELCC** — see below; storage at duration-ELCC) cannot fall below the shared adequacy requirement (`resolve_adequacy_requirement_mw` — the published FPR where one exists, held-last beyond the last published delivery year (card C-A 2026-08-25), else `peak_demand × (1 + PLANNING_RESERVE_MARGIN_BY_ISO)`) — the same requirement the step-6 build backstop tests (one requirement, two verbs). If economic retirements would breach it, eligible units are un-retired cheapest-firm-adequacy-first ($/firm-MW-yr ascending, CO₂-rate tie-break), and every retention is recorded in the `floor_retention_log` persisted per year (`floor_retentions.json`).

**VRE accreditation (CR-3.1, penetration-indexed ELCC):** wind/solar (and any published VRE class) accredit through one resolver (`capacity.resolve_renewable_capacity_credit`, gate `ScenarioConfig.renewable_elcc_curves`, default **on**) with a three-step ladder: (1) the ISO's own published penetration-indexed ELCC curve (`RENEWABLE_ELCC_CURVES_BY_ISO`, digitized from the P-0B `capacity-market-elcc` datatype — PJM BRA final class ratings on an installed-MW axis, MISO's capacity-credit-vs-penetration-of-peak curve, NYISO's single-point CAFs), evaluated piecewise-linearly (flat-clamped beyond the published domain) at the **model's own installed share** — the class's ISO-wide nameplate (pools + fleet units) against the year's peak — so accreditation responds to modeled build and VRE saturates its own capacity value (rule 13 `[R-MEASURED]`, zero fitted parameters); (2) a published single-point per-ISO override (`RENEWABLE_CAPACITY_CREDIT_BY_ISO` — ERCOT's CDR ELCC basis, unchanged); (3) the generic flat constants (`RENEWABLE_CAPACITY_CREDIT`, wind 0.16 / solar 0.18) as the cited neutral fallback for ISOs with no ISO-published study (NEISO — third-party studies only; CAISO — the CPUC study publishes incremental-basis values misaligned to a fleet-average ledger). All four consumers move together off the one resolver: `accredited_firm_capacity_mw`, the reliability floor, the reserve-margin backstop, and the CR-1 reserve position. `renewable_elcc_curves=False` is the frozen-penetration byte-compat mode (pre-CR-3.1 flat credits — the capacity-hindcast baseline arm). Storage is deliberately untouched: its accreditation keeps its own single stack (duration-ELCC × entry-screen saturation derate × portfolio dilution, §5.5) — one mechanism per phenomenon (rule 19 `[R-ONE-MECH]`).

**Announced-retirement reversal supersession:** a plant whose confirmed-retirements registry rows are ALL `superseded` (a public counter-instrument reversed the exit outright — e.g. Byron/Dresden's 2021 announced dates reversed by IL CEJA, P.A. 102-0662) has its stale EIA-860 announced date ignored by step 1, any fuel; the unit stays with the economic screen. Data-driven and independent of `confirmed_exits_enabled` — honoring a documented reversal is a data correction on the announced channel, not an exit injection (`data.confirmed_retirements.load_announced_reversal_plants`).

**Sector gate (`retirement_sector_gate`, GATED default off; ARMED FOR MISO ONLY via `iso_configs` `default_scenario_overrides` by owner instruction 2026-09-05 on the measured A/B, rule 25 `[R-ISO-SCOPE]` — capx D53):** which owners face the screen at all. The screen models a *merchant* decision (attainable margin vs going-forward FOM), while a regulated utility's exit is an IRP / rate-case outcome carried by the owner-filed EIA-860 Schedule-3 date (step 1b) or a public instrument (step 0) — on MISO's 2021–2025 record 88–92 % of the coal / gas_st / oil exit MW was regulated-utility (`FINDING-capx-d32-floor-retention-2026-09-02.md` §4.3). Armed, every thermal unit whose PLANT's EIA-860 `Sector` (read from the run's active vintage, `data.fleet.eia860_plant_sectors`) is **1 — Electric Utility** is exogenous to the screen and exits only through steps 0 / 1 / 1b; sectors 2–7 (IPP, commercial, industrial; CHP and non-CHP) face the screen as before, and a plant absent from the vintage table fails OPEN to the screen. Rule 19: neither declaration (dated plant, sector 1) produces an exit, so a gated unit is never decided, entry-capped or pipelined and the floor / admission cap / backstop count it as ordinary surviving fleet; the year's gated set is ledgered (`sector_gated`). **Exit-exempt, not offer-exempt (capx D78, owner ruling Q53 = reading 1, 2026-09-06):** the gated ids enter the screen on their own parameter, `exit_exempt_unit_ids` (`retirements.sector_gated_unit_ids`, the twin of `dated_plant_unit_ids`), so a sector-1 unit is still *evaluated* and still *offers* its accredited MW into the §5.9 capacity clearing at its net-ACR cap — PJM's must-offer requirement (Manual 18 Rev 62 §1.2 / §5.4.1 / §5.4.7) keys on existing-and-in-footprint, and its three enumerated exceptions (physical CP incapability, a firm external sale, a filed removal of Capacity Resource status) never on ownership — and leaves `margins` only after the clearing, on the decision side. Before D78 the ids rode the dated-plant `exempt_unit_ids` union and silently stopped offering wherever the clearing is armed (`FINDING-capx-d58-2026-09-06.md` §3: 34.2 GW of PJM utility capacity became $0 price takers and the 2022 clearing price fell 9.67 %); with the clearing off (MISO) the two constructions are byte-identical. A gated unit the auction does not clear is *uncleared and retained* (design `DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md` §2.4), never forced. A partition on one published per-plant attribute, no weight (rule 21 `[R-DOF]`); `Regulatory Status` is not consulted. Design, census, interactions (confirmed exits, RPS-credited and merchant nuclear, the CHP sectors, utility-owned merchant affiliates) and the named-not-built additions-screen mirror: `docs/handoffs/DESIGN-capx-d53-sector-gate-2026-09-05.md`.

**Design note:** Sigmoid retirement was considered and rejected in favor of fully economic retirement with fuel-type-aware thresholds. The economic approach is more transparent — every retirement is traceable to a revenue shortfall — and avoids the arbitrary sigmoid midpoint parameter. The coal FOM multiplier (1.3×) captures the non-economic pressures (regulatory risk, ESG) that the sigmoid was designed to model.

### 5.3 Economic New Entry

Screen by technology: if `expected_revenue > LCOE`, the technology is economic for entry.

- Expected revenue estimated from prior year’s price duration curve. Dispatchable thermal candidates use the price-duration integral `Σ_t max(0, price_t − var_cost, r_t)` — with the same hourly reserve-price signal the retirement screen sees (`screen_reserve_value_enabled`; a new CT is a Non-Spin-tier quick-start, a new CC synchronized), which then supersedes the annual AS credits (rule 19 `[R-ONE-MECH]`). Wind/solar candidates value their **build zone's hourly CF profile against that zone's prices** (shape-aware capture, incl. each tech's actual share of scarcity-priced hours — plan §6 CX-6c), falling back to the scalar base-CF screen when profiles are unavailable.
- LCOE from technology cost assumptions with learning curves (Tier 2 parameters)
- IRA credits reduce LCOE (PTC for wind, ITC for solar/storage — Tier 1 parameters)
- Annual build rate capped per technology (e.g., ERCOT ~12 GW/yr queue throughput)
- Clean candidates earn an attribute payment as additional expected revenue: `max(effective EAC, prior-year RPS shadow price)` × expected MWh, where the effective EAC is `max(legacy eac_price_*, federal CES premium × tech credit fraction)` for the screen year (`policy/federal_ces.effective_eac_price_for_tech`, §1.4 — under the CES, `nuclear_smr`, `hydrogen_ct`/`hydrogen_ccgt` and `gas_cc_ccs` candidates earn the premium; the RPS dual is credited to RPS-eligible renewables only), so a binding RPS or a federal premium pulls more clean entry across the LCOE hurdle
- Technology priority: ranked by revenue-minus-LCOE margin, highest first

**Technology availability gating.** The candidate set is not fixed. The classic four technologies (wind, solar, gas CC, nuclear) are always eligible, but each emerging technology (hydrogen turbines, CCUS, enhanced geothermal, offshore wind — see §1.5) joins the candidate pool only once the simulation year reaches its configured availability year (`h2_available_year`, `ccs_available_year`, `egs_available_year`, `offshore_wind_available_year`). Offshore wind additionally enters only in ISOs listed in `offshore_wind_eligible_isos`. The screening order is therefore: (1) build the year's eligible candidate set, (2) compute each candidate's LCOE and margin, (3) rank and build subject to queue caps. Hydrogen turbines and CCUS share the `gas_cc` per-tech queue cap (shared gas-turbine supply chain); geothermal and offshore wind have their own per-tech caps.

### 5.4 Known Pipeline

EIA-860 provides: units under construction (with expected online date), announced retirements (with expected date). These are deterministic — they happen regardless of economics. Transition point from known to modeled: ~2030 for near-term pipeline, model takes over for years beyond the data horizon.

**As built** (`data/fleet/eia860.py::load_planned_additions`, forecast mode only): proposed-generator rows with a construction-committed status (`U`/`V`/`TS` — `P` planned-with-permits is excluded as too speculative for a firm thermal unit, though the renewables capacity-ramp aggregation does count it), whose plant's balancing authority maps to the running ISO and whose `Effective Year` falls after the operable-snapshot vintage (`EIA860_OPERABLE_VINTAGE`, currently 2025 per the EIA-860 2025 Early Release), enter the fleet as `Generator`s (`unit_id` prefixed `planned_`) in their effective year. Wind/solar/storage rows are skipped — renewable growth lives in the zonal capacity pools and storage in its own screen, so adding them here would double-count. Zones come from the plant's EIA-860 lat/lon. Units already due by the first simulated year join the base fleet; later ones are injected by `evolve_fleet` step 3.

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
terms. **Exactly one mechanism supplies it (rule 19 `[R-ONE-MECH]`), keyed on
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
rows (`lp/reserve_rows._build_reserve_rows`), and the ERCOT reserve design marks storage
`storage_eligible=True`, so once `energy_reserve_coopt` is on in the forecast
runner the battery trades energy against AS on its own power cap and cannot
dump its full cap into the top arbitrage hours it must back AS in. The measured
per-hour storage AS reservation (`storage.reserve_storage_as_power`) stays
**backcast/calibration-only** (rule 13 `[R-MEASURED]`).

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

Beyond *new* `gas_cc_ccs` entry (§1.5.2), existing gas-CC units can be **retrofitted** with post-combustion capture (`model/capacity.py::apply_ccs_retrofit`, gated on `ccs_retrofit_available_year`, default 2028). Redesigned in W2-C (national-ces-eac-premium-plan §11, owner-resolved 2026-07-17); the former fixed-0.55-CF payback screen is superseded.

**The joint retrofit-or-retire choice.** The screen runs at evolve-fleet step 2, BEFORE the economic retirement screen (§5.1 step order note): each year, every gas-CC unit with at least `ccs_retrofit_min_remaining_life` (15) years of useful life left is offered the retrofit continuation before the exit. A unit retrofits when the retrofit **beats staying unabated** and its **windowed payback clears the remaining life**; it retires only when both continuations fail (the loss-year counter semantics of §5.2 are unchanged for everything that does not convert). A profitable retrofit fires on a healthy unit too — under §45Q plus a CES premium a unit may convert well before distress.

**Economics — attainable margin at the post-retrofit cost basis.** Both continuations are valued as attainable (pro-forma) inframarginal margins over the prior year's hourly capacity-screen price signal — the same construction as the retirement screen (§5.2), so anticipated utilization is **endogenous** (no fixed screen CF: with the credits as bid offsets the post-retrofit effective cost clears the price-duration curve near-baseload-deep exactly when the economics say so). Per MW-yr, with `avail = 1 − EFORd`:

```
mc_unabated  = hr·gas + vom + er·carbon
mc_post      = hr·(1+hr_penalty)·gas + vom + vom_adder
               + er·(1−capture_rate)·carbon + captured·co2_transport_storage_cost
m_unabated   = Σ_t max(0, p[t] − (mc_unabated − attr_unabated)) × avail
m_window     = Σ_t max(0, p[t] − (mc_post − attr_post − q45)) × avail
m_post       = Σ_t max(0, p[t] − (mc_post − attr_post)) × avail
uplift_window = m_window − m_unabated − ΔFOM
uplift_post   = m_post   − m_unabated − ΔFOM
```

- **Attribute term** `attr_*` (one per state): `max(legacy eac_price_gas_cc_ccs, federal CES premium × credit fraction)` via `policy/federal_ces.effective_eac_price_for_unit` — the certificate is sold once (§1.4 max() rule). The valuation is **incremental over the best unabated state**: under `cesa_ci` the unabated CCGT's own partial credit (`attr_unabated`) is netted out; under `clean_capture` it is 0 and the full post-retrofit credit is the uplift.
- **§45Q** (`q45`, `policy/ira.ccus_45q_credit_per_mwh`: $85/t × captured t/MWh) **stacks on top of the certificate** — a tax credit is a separate instrument from an EAC (plan §11 Q1); no tonne is double-counted within either instrument. Eligibility is gated on `ira_ccus_45q_last_year` at the retrofit (commit) year — a begin-construction-deadline proxy that never truncates an earned stream.
- **Credit window** (`ira_45q_credit_window_years`, statutory 12 — 26 U.S.C. §45Q(a)(3)-(4); `None` = owner's indefinite-extension scenario): the payback is **two-segment** — the cumulative uplift runs at `uplift_window` for `min(window, remaining_life)` years and `uplift_post` afterwards; if the credit expires before recovery and `uplift_post ≤ 0`, the retrofit never pays back. The **same window levelizes the §45Q term in the new-build CCS LCOE** (`_emerging_lcoe`): the credit is scaled by `CRF(life)/CRF(window)` — PV-consistent at the screen's discount rate — a deliberate behavior change from the former un-windowed new-build treatment.
- `ΔFOM` is the going-forward fixed-cost delta between the states (`fixed_om_gas_cc_ccs` vs `fixed_om_gas_cc`, each × its retirement FOM multiplier — the same fields §5.2 prices each state at). Capacity/AS revenue is state-invariant for the same MW and nets out of the incremental comparison.

**Mechanics (unchanged).** A converting unit's `heat_rate` gains `ccs_retrofit_hr_penalty` (12%), `vom` gains `ccs_retrofit_vom_adder` ($8/MWh), the emission rate drops by `ccs_retrofit_capture_rate` (90%), and `fuel_type` flips to `gas_cc_ccs` in place (same unit_id, zone, MW). Retrofit capex (`ccs_retrofit_capex_kw` = **1,521.4 $/kW in constant 2026$** — the NREL ATB 2024 **capture-island increment** the model's own new-build CCS already carries, i.e. `NEW_ENTRY_COSTS["gas_cc_ccs"]` 3,104.7 − `NEW_ENTRY_COSTS["gas_cc"]` 1,583.3, both from the committed ATB extract via `scripts/data/derive_entry_costs_from_atb.py`; it superseded a shipped 900.0 that carried no stated dollar-year) follows the same Wright's-Law learning curve as new CCS and retrofitted GW feeds the shared experience base. Candidates rank shortest-payback first up to `ccs_retrofit_max_gw_per_year` (3 GW/yr) per ISO; **cap-displaced candidates stay unabated on the normal loss counter and re-screen next year**. Converted units clear their loss counters and skip that year's retirement screen. The screen requires the prior-year price signal (first simulated year skips, like every price-driven screen).

**Capex sized to the host's CO2 flow (capx D50, `ccs_retrofit_capex_co2_scaling`, DEFAULT ON since 2026-09-05 — owner ruling Q42 on the D50/D50-R A/B, executed by capx D60 as a (b′-1) declared default flip; an explicit `False` still selects the pre-flip construction and keeps its cache key).** Unarmed, the capture island is charged at `ccs_retrofit_capex_kw` FLAT per kW for every host while `q45` is credited on the host's own captured tonnes — a construction seam (`docs/handoffs/FINDING-capx-d49-2026-09-04.md` §1.4): the credit scales with CO2 per MWh, the capex does not, so the retrofit margin rises with host emissions and a merchant CC at 0.55 t/MWh clears on §45Q alone. Armed, (a) `retrofit_capex_per_mw = capex_kw × 1000 × captured / captured_ref`, with `captured_ref = capture_rate × hr_ref × 0.057 = 0.323 t/MWh` and `hr_ref = min(HEAT_RATE_BINS["gas_cc"]) = 6.3` — the same reference host the new-build CCS LCOE charges the ATB increment against (`ccs.py::ccs_retrofit_captured_ref_t_per_mwh`; zero DOF), applied after the Wright's-Law learning of the reference increment; and (b) cogeneration hosts (`plant_group == "CC_CHP"`) are not candidates — the published island cost bases are electric-only NGCC costings and a CHP's CEMS rate per net electric MWh charges the steam host's fuel to electricity. Off is byte-identical, and so is **every horizon that ends before `ccs_retrofit_available_year` (2028)**: `ccs.py::apply_ccs_retrofit` returns at its first statement, before any read of the flag, and that call site is the field's only consumer — hence no backcast, hindcast or crossover run moves. The ΔFOM and the capture VOM adder stay reference-host-sized under (a), so the clearing threshold in host emissions moves rather than vanishes (recorded in `PREDECL-capx-d50-2026-09-04.md` §1.2). **ARMED AS THE DEFAULT POSTURE for all six ISOs on 2026-09-05** (owner ruling Q42, director sitting r#37, on `FINDING-capx-d50-2026-09-04.md` §8; execution record `FINDING-capx-d60-2026-09-05.md`). It carries no ISO's fitted number — every term is an already-cited constant — so it is a posture rather than a transfer and rule 25 `[R-ISO-SCOPE]` is untouched. The measured signature is an asymmetry rather than a level: at carbon 0 the repair closes the screen (ERCOT 3.79 GW → 0; PJM 5.74 → 0 in 2028; MISO 4,631.1 MW → 0 across the window) and under RGGI it does not (NEISO 12.79 → 12.38 GW, 96 % of the eligible fleet), because the avoided-carbon leg of the uplift is per tonne too and a per-tonne island cannot outrun it.

**Known simplifications.** Post-retrofit *dispatch* offers do not carry the §45Q offset (dispatch bids are `mc − attribute credit` only, §1.4), so realized CF can run below the screen's anticipated CF; and the §5.2 retirement screen does not credit §45Q revenue to already-retrofitted units in later years (no per-unit credit-window vintage tracking). Both understate CCS economics conservatively; revisit if retrofit retention misbehaves in campaign runs. With §45Q in the screen, **retrofits are now possible in BAU** — that is the point of the redesign: a premium-case retrofit is attributable to the premium, not to a missing statutory credit.

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
**structural mechanism** (rule 1 `[R-STRUCT]`): it belongs regardless of backcast
fit, is never fitted to the residual, and is **never enabled in a keeper** —
preferring the published limit over a calibrated scalar can move the
backcast (rule 14 `[R-ACCURATE]`), and that is expected, not a reason to revert.

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
and `tests/unit/config/test_capacity_area_crosswalk.py` /
`tests/unit/data/test_capacity_deliverability_wiring.py` for the coverage tests.

### 5.9 Capacity-Market Revenue — Fixed Price and the CR-1 Sloped Demand Curve

In a capacity-market ISO a qualifying resource earns a resource-adequacy
payment *outside* the energy market (Module M1), which the three
capacity-evolution screens credit as revenue: economic retirement (§5.2),
thermal new entry (§5.3), and storage new entry (§5.5). All three price
adequacy through **one seam** — `MarketDesign.capacity_price_per_firm_mw_yr`
(rule 19 `[R-ONE-MECH]`, one curve per ISO, no screen-specific curves) — which returns a
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
`firm_peak × FPR`; PJM 2025/26 = 0.9380, 2026/27 = 0.9170, 2027/28 = 0.9260,
2028/29 = 0.9401). Beyond the ISO's **last** published FPR the resolver
**HOLDS-LAST** (owner-signed convention, card C-A 2026-08-25 — the
`resolve_demand_curve_vintage`/`forward_net_cone_anchor` forward-carry precedent),
so a forecast horizon never drops off the published series onto the stale
composite mid-horizon; the hold is superseded per delivery year on publication
(rule 23 `[R-FROZEN-DERIVE]`). It falls back to `firm_peak × (1 + PRM) × icap_to_ucap_ratio` only for
an ISO with no FPR table or a delivery year before the table's first entry — so
those cases are byte-identical to the pre-migration construction.

**Fixed mode.** The seam returns the flat `net_cone_per_kw_yr × 1000`, the
per-ISO net-CONE anchor every qualifying MW earns when the clearing gate is off.
FF-2C R4 (2026-07-20) re-derived every anchor to the ISO's **published basis**
(CAISO 88.08 = CPM soft-offer cap / PJM 77.431 = UCAP net-CONE / ISO-NE 108.94 =
FCA 18 / MISO 79.8 = North/Central Net CONE $/kW-yr; NYISO 110 unchanged) — for
the curve ISOs the fixed anchor now equals the published curve anchor. This is
the active price only where the gate is off (NYISO, and any unflipped ISO); it
does not respond to the fleet.

**CR-1 sloped demand curve** (`ScenarioConfig.capacity_market_clearing` /
`capacity_market_clearing_by_iso`, resolved per ISO through
`resolve_capacity_market_clearing`). **Default ON for PJM/MISO/CAISO/NEISO**
(FF-2C flip, owner sign-off 2026-07-19 — the CR-1 curve is the resource-adequacy
price for those four ISOs in forecast mode); OFF for NYISO (curve-ineligible
until R5a) and ERCOT (energy-only). A plain backcast coerces the mapping to
`None` (no capacity evolution runs there, so keepers stay cache-byte-identical);
a hindcast arms it per leg. When on, the fixed price is replaced by the market's
own **net-CONE-anchored sloped demand curve** evaluated at the model's own
accredited reserve position:

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
60.396 that mis-scaled the UCAP curve by PJM's ~0.78 factor). The legacy fixed
`net_cone_per_kw_yr` anchor was kept distinct for pre-flip default byte-identity;
**FF-2C R4 (2026-07-20) reconciled the two — the fixed anchor is now re-derived
to the same published basis as the curve anchor for every curve ISO.** The
`requirement_mw` and the accreditation are the **exact same** ones the
retirement reliability floor and the reserve-margin backstop compute
(`capacity_reserve_position` calls `resolve_adequacy_requirement_mw` — published
FPR where available, held-last beyond the table (card C-A), else `(1 + PRM) ×
ratio` — and `accredited_firm_capacity_mw`
— one requirement, one basis, rule 19 `[R-ONE-MECH]`); the runner computes the position **once**
on the entering-year fleet and threads the one value into all three screens. So the capacity price now *responds to the fleet*
the way real markets do — it collapses toward zero when the system is long (RA
saturated) and rises toward the cap when short — which a fixed price structurally
cannot.

Every curve number is a **published market-design parameter** (rule 13 `[R-MEASURED]` — never a
fit target), sourced from the `capacity-market-demand-curve` datatype
(`data/raw/capacity-market/demand-curve`): PJM's VRR points + Net CONE + price
cap (2026/2027 BRA), NYISO's ICAP demand curve (2025-2026 NYCA reference point +
12% curve length, modeled annually), ISO-NE's FCA Net CONE + starting price
(FCA 18) with the reserve-position geometry from FCA 11's published curve, and
MISO's PRA Net CONE + gross CONE (the **seasonal** RBDC — see below). CAISO has no
centralized auction, so it keeps the fixed proxy in **both**
modes (re-cited to the CPM soft-offer cap / CPUC RA report — the documented
low-fidelity registry member). The encoded constants are reconciled against the
datatype in `tests/unit/model/test_capacity_demand_curve.py`.

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
explicitly **not** invented (rule 13 `[R-MEASURED]`). Pre-RBDC MISO years (PY2009-10 .. PY2024-25)
were a **vertical** curve capped at CONE (FERC ER23-2977) — represented as a
near-vertical step anchored on gross CONE, not a sloped shape.

**Curve eligibility (RC-1C).** A governance gate layered on the clearing gate:
`resolve_capacity_curve_eligible(iso)` (`CAPACITY_CURVE_ELIGIBLE_BY_ISO`) blocks an
ISO from pricing on its sloped curve until its accreditation-pairing basis is
owner-signed. **NYISO is INELIGIBLE** — its ICAP→UCAP translation-factor pairing
(R5a) is adjudicated but not owner-signed
(`docs/handoffs/nyiso-neiso-capacity-pairing-adjudication-2026-07-15.md` §3) — so
even with the gate on and a vintage resolved,
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
flat anchor (rule 13 `[R-MEASURED]` — never fabricate an unpublished point). The vintage equal to
the registry reference reuses its exact curve/anchor object, so pricing that year is
byte-identical to the fixed registry curve. Every vintage number is reconciled
against the datatype in `tests/unit/model/test_capacity_demand_curve.py`.

Capacity revenue (fixed or curve, labeled by source) is also reported per plant
in `results/plant_financials.py` (`capacity_revenue` +
`capacity_revenue_source`). **This session lands the mechanism default-off
only**; flipping the default is gated on the CR-2 auction-history validation
(`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §3.3).
Explicitly out of scope for CR-1 (revisit on CR-2 evidence): CP/PAI penalties,
Y-3 forward lag, and locational LDA-specific curves (composes later with §5.8
part B). Full supply-curve auction clearing with unit offers — the first of the
original out-of-scope items — is now the GATED supply-clearing mode below.

**Supply-clearing mode — the clearing half (capx D57, 2026-09-05;
`ScenarioConfig.capacity_market_supply_clearing_by_iso`, a `{iso: bool}`
sibling of the curve gate resolved through
`config/capacity_market.resolve_capacity_market_supply_clearing`, which also
REQUIRES the curve gate ON for the ISO; the dataclass default stays `None`, and
PJM is ARMED — together with the two D48 accreditation-design fields — through
`iso_configs.py::_pjm_config` `default_scenario_overrides`, owner ruling
2026-09-05 on the D57 A/B, so only PJM's forecast posture carries it and every
other ISO and every backcast keeper is byte-identical).** The curve mode above evaluates the
published curve at the installed-fleet *census* position and broadcasts that
price to every unit. PJM's RPM does not: every existing unit must submit a
sell offer capped at its net Avoidable Cost Rate (gross ACR minus E&AS net
revenue, on UCAP — Manual 18 Rev. 62 §5.4.1 / §5.4.4 / §5.4.8.4(B), Tariff Att.
DD §6.4 / §6.8), the offers form a supply curve, the auction clears where it
meets the VRR curve, cleared MW earn the Resource Clearing Price and uncleared
MW earn nothing (§5.7.1). Armed, the retirement screen
(`retirements.py::_settle_capacity_supply_clearing`, once per screen year after
its margin loop) builds, for every screened thermal unit, `offer_g = max(0,
GFC_g − EAS_g) / (A_g × 365)` $/MW-day from its OWN two operands — the
going-forward cost above and the pre-capacity pro-forma margin — on the ISO's
accreditation seam (`_thermal_firm_mw`, devintaged under §5.9's D48 gate);
every other accredited MW the ledger counts (VRE / hydro / storage / firm
imports / DR / screen-exempt dated plants and this-year retrofits) enters as a
$0 price taker, `Q_0 = accredited_firm_capacity_mw − Σ A_g` on the screen's own
fleet; the stack clears against the delivery year's vintage curve through the
SAME `capacity_price_per_firm_mw_yr` seam (`adequacy.py::
clear_capacity_supply_stack` + `capacity_supply_curve`: price at the
intersection — the curve between offers, or the marginal offer inside a step
by bisection; the marginal unit is cleared in full, the screen's whole-unit
grain); and the capacity leg is settled per unit — cleared: `price × 365 ×
A_g`, uncleared: $0. Hence a screened unit passes the bar **iff it cleared**:
the screen's failing set IS the auction's uncleared set (design §3.5), and
the pipeline's admission cap sizes a cohort the market would not buy instead
of one priced at $0. The thermal-entry and storage-entry screens read the
clearing price as PRICE TAKERS through a pre-priced `ClearedCapacityPrice` in
the same `reserve_position` slot (entry does not offer into the stack — that
would decide entry twice, rule 19 `[R-ONE-MECH]`). With every offer at $0, or the curve above
every offer (a SHORT market — every forward year on the 2028/29+ collar for
gas and oil), the clearing reduces to the census evaluation exactly (invariant
I1); the census evaluation is REPLACED, never stacked. Zero free parameters:
no offer adder, floor, shading factor, E&AS haircut or per-fuel cap, and the
published default gross ACR table is not used. Ledger: an additive
`capacity_clearing` block per `evolution_<year>.json` (price, cleared MW and
position, price takers, uncleared by fuel, the whole offer stack) and per-row
`capacity_offer_usd_per_mw_day` / `capacity_accredited_mw` /
`capacity_cleared` on `pipeline_events`. What it measures rather than
repairs (pre-declared, PREDECL-capx-d54 §2 + the D57 addendum): on the
committed hindcast operands the cleared position lands within 0.7 / 1.0 / 2.6
points of the published cleared position for 2022/23–2024/25 while the price
lands 1.7× / 2.4× / 5.5× the published price, because the gas-CT / gas-ST /
oil fleets carry zero E&AS margin in the hindcast prices and offer at their
full bars — the E&AS operand's signature, reported at full magnitude (rules 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` /
21 `[R-DOF]`). Generic in form, PJM-scoped by data (rule 25 `[R-ISO-SCOPE]`; NYISO's spot
market literally evaluates its curve at a census quantity, so its clearing
half is a supply-census question). Records: `DESIGN-capx-d54-pjm-clearing-
half-2026-09-05.md`, `PREDECL-capx-d57-2026-09-05.md`,
`FINDING-capx-d57-2026-09-05.md`.

-----

## 6. Parallelism & Performance

### 6.1 Parallel Execution

Independent work units: `(scenario_config, iso)` pairs. Within each work unit,
years run **sequentially** — capacity evolution makes year N+1 depend on year N,
and the year loop in `runner.py` is deliberately not parallelized.

The fan-out lives in one place, `pipeline/members.py`. Sweeps, weather/sampler
ensembles, the scenario matrix and the PB-5 slice drivers all expand a scenario
set into `(config, iso)` pairs and solve them across a process pool:
`run_pairs` is the core (each pair may carry its own ISO, as a cross-ISO sweep
does) and `run_member_configs` is the single-ISO `{member_id: config}`
convenience. `stride` — an `(offset, step)` pair — runs only `items[offset::step]`,
so two invocations partition the member set with zero overlap.

**The worker count is capped by rule 12 `[R-PARALLEL]`, and that cap is
enforced by default.** `DEFAULT_MEMBER_CAP = 2`: a forecast member on a
per-plant ISO uses several GB (§6.3), so more than ~2 concurrent members OOMs.
`workers=None` resolves to `max(1, min(cap, cpu_count() - 1))`. An explicit
`workers` is **honoured as given** on `sweep`/`ensemble` (the caller owns that
risk); `matrix.run_matrix` clamps its own explicit value before delegating.
`workers == 1` runs the members in-process. Before this module existed,
`run_sweep` carried its own copy of the pool-open dance defaulting to an
**uncapped** `cpu_count() - 1` — that default was the rule-12 violation this
module removed, and it is why no illustrative `ProcessPoolExecutor(max_workers=N_CORES)`
snippet appears here.

### 6.2 Performance

**Measured wallclock is not pinned in this document.** Per-phase ground truth —
cold vs warm solve times per ISO-year, the P0/P1 split, the solve share of a
year — lives in `docs/handoffs/wallclock-baseline-2026-07.md`, which is
maintained against the code. A number transcribed here rots; this section
carries only the durable structural facts.

- The **cold P0 solve dominates**: it is roughly three-quarters to four-fifths
  of a scenario-year's wallclock. Matrix construction and result export are the
  remainder.
- The **obvious solver levers are benched and rejected on record** — IPM plus
  crossover, thread scaling, HiGHS parallel/PAMI, presolve-on. None beat the
  shipped dual-simplex configuration on this problem's shape; do not re-sweep
  them without new evidence.
- The **warm-start levers are shipped and load-bearing** (§6.4).
- Throughput scales with `[R-PARALLEL]`'s ≤2-member cap (§6.1), not with core
  count.

### 6.3 Memory Management

Each worker builds and discards the LP per year. Do not accumulate LP objects
across years. The HiGHS instance is created fresh per solve (or cleared with
`h.clear()`). Only the result arrays (dispatch, prices, emissions) persist in
memory during the year-loop, and they are written to Parquet immediately.

**Size the machine from the measured envelope, not from the structure.** A
full-8760 solve on a per-plant, multi-zone ISO carries a resident set in the
**low tens of GB**, not the single-digit GB the block structure might suggest —
which is exactly why `[R-PARALLEL]` caps concurrent members at 2 (§6.1) rather
than at core count. Current per-ISO figures live with the wallclock baseline
(§6.2) and in the per-run PRECOMMIT records, which report RSS alongside timing.

Two construction invariants keep that envelope from growing (§2.3): the builder
never materializes a Python-object view of the fleet (rule 6 `[R-SOA]`), and it
never allocates per-hour (rule 2 `[R-VECTOR]`) — the CSC arrays are counted
analytically and filled once.

### 6.4 Warm-Start

Two warm-start layers are shipped, both basis-level and both **validated
basis-neutral** — the objective, every zonal price and total generation are
bit-identical; the only movement is the marginal-tie reshuffling the intra-year
warm start already carries.

- **Intra-year.** Successive solves within one year (the P0→P1 seam) reuse the
  prior basis.
- **Cross-year** (`MARKET_SIM_WARMSTART_XYEAR`). Each year's optimal basis
  warm-starts the next year's cold P0 solve. It is **ON by default on the
  calibration path**, worth roughly 2.3× on warm years. Precedence, highest
  first: `run_calibration.py --no-xyear-warmstart` forces OFF; an explicitly-set
  `MARKET_SIM_WARMSTART_XYEAR` env var is honoured as-is; otherwise ON. The
  resolved value is written back to the environment so the shared solve core
  (`pipeline/solve.py::run_energy_solve`) reads one answer.
- The **persisted year-1 basis** lets a re-run skip the cold start entirely.

See `docs/cross-year-warmstart.md` for the validation record and the backlog.

### 6.5 Byte-Identity as a Reproducibility Contract

What may change about the model is governed by a golden-artifact protocol, not
by reviewer judgement. `scripts/capture_keeper_goldens.py` captures a keeper's
outputs before a change; `scripts/regression_gate.py --mode byte` compares after
it at `atol = rtol = 0`. Pure code motion must clear byte mode; a deliberate
builder swap runs at `--mode builder` (`1e-9`) and says so.

**A golden FAIL is a finding, never grounds to regenerate the golden.** That
asymmetry is the whole contract: it is what lets a refactor, a module split or a
default flip be asserted as behaviour-preserving rather than merely believed to
be. Its companions are the cache-key epoch discipline (§4.1) and the
declared-default-flip protocol — a flip that moves keys declares its epoch, and
a flip that does not move keys (an optional-registered field at its live
default) is visible only in the ledger.

The full protocol, the two golden systems and the run lanes are specified in
`docs/testing.md` and `docs/refactor-consolidation-plan-2026-07.md` §8.

-----

## 7. Governance

The model's binding engineering rules are **not restated here**. They live in
`CLAUDE.md` as numbered non-negotiables with stable `[R-*]` IDs, and this
document cites them by ID (rule 5 `[R-NO-MAGIC]`, rule 2 `[R-VECTOR]`, rule 6
`[R-SOA]`, rule 7 `[R-PARQUET]`, rule 3 `[R-RENEW-VAR]`, and the rest). A second
copy in the spec would be a duplicate authority that drifts — which is exactly
what happened to the copy this section used to hold, and why it was retired at
finalization.

The rules most often needed while reading this document, with the sections that
depend on them:

| Rule | Where it binds in this spec |
|---|---|
| 1 `[R-STRUCT]` | Right market structure first; backcast fit is not the objective (§1.8, §5.8) |
| 2 `[R-VECTOR]` / 6 `[R-SOA]` | Construction invariants (§2.3), memory envelope (§6.3) |
| 3 `[R-RENEW-VAR]` | Renewables are decision variables (§1.1) |
| 4 `[R-DUALS]` | Prices are duals (§1.3, §1.9) |
| 5 `[R-NO-MAGIC]` / 24 `[R-REGISTRY]` | Tiered parameter system (§4.1) |
| 7 `[R-PARQUET]` | Result storage and caching (§4.4) |
| 8 `[R-8760]` / 9 `[R-EPSILON]` / 10 `[R-ONE-PASS]` | LP shape (§1.2, §1.9, §5.1) |
| 12 `[R-PARALLEL]` | Member cap and the sequential year loop (§6.1) |
| 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` | Measured-input admissibility (§1.7, throughout §5) |
| 19 `[R-ONE-MECH]` | One mechanism per phenomenon (§1.6, §5.2, §5.5, §5.9) |
| 23 `[R-FROZEN-DERIVE]` | Frozen derive scripts (§3.3, §5.9) |
| 25 `[R-ISO-SCOPE]` | Tuned curves never cross ISO boundaries (§1.3, §3.3, §5.6) |

Rule numbering, the audit-ordinal mapping, per-rule amendment genealogy and the
incident record are in `docs/governance/rule-history.md`.
