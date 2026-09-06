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
the required renewable fraction (0–1), or `None`. RPS is **not** a force-build
step — it is an annual LP constraint (`_build_rps_row` in `model/lp/rows.py`):
`Σ(W + S + statute-eligible P) + ACP ≥ rps_target · Σ demand`, nuclear never
admitted (CX-6a — a clean tier that counts nuclear is the separate clean-tier
family below). **Its dual is the REC shadow price**
(`DispatchResult.rps_shadow_price`), capped by the ACP escape, which competes with
exogenous EACs in capacity economics (`max(eac_exogenous, rps_shadow_price)` — no
stacking). MISO replaces the ISO-wide row with K per-state compliance-region rows
(`build_rps_region_arrays`, `miso_rps_compliance_regions`).

### Clean-tier row family (`clean_tiers.py`) and the federal CES target row (`federal_ces.py`)

A **second, independent row family** on the same K-region machinery
(`_build_rps_region_rows`), each row `Σ credited MWh + escape ≥ share · obligated
load` with its own ACP-style escape; nuclear is admitted. Two producers compose
into one `CleanRegionArrays` through `append_clean_region`, in region order:

| Region | Producer | Mask / RHS | Qualifying spec | Escape |
|---|---|---|---|---|
| MN carbon-free, MI clean (MISO, `miso_clean_tier_rows`) | `build_clean_region_arrays` | statute zones / obligated-load share × target | fuel-name tuple (indicator coefficients) | `STATE_RPS_ACP` proxy |
| **Federal CES target** (`federal_ces_target_by_year`, any ISO) | `append_federal_ces_region` | every load zone / `target(year)` on every zone | `(n_gen,)` credit-fraction vector = `unit_credit_fractions` (both crediting modes; a CCS column carries 0.95) | `federal_ces_acp_usd_per_mwh` |

Since SCN-WS2a the family **stands alone or beside either RPS grain** (the former
"requires the RPS region family" coupling is relaxed; escape slots follow whichever
RPS escapes exist). `runner._clean_region_arrays_for_year` is the single resolver
of the region list, used by the solve-side arming and the cached-year dual mapping
alike. Each row's dual is that region's clean attribute price;
`clean_credit_by_fuel` maps it to `{fuel: (n_zones,)}` (a vector-form region at
`dual × fraction` from its `fuel_credit` map) and the screens take it through the
existing `max(EAC, RPS dual, clean dual)` — no new consumer.

**Federal CES — two mechanisms, one at a time (rule 19).** `federal_ces_enabled`
is the master crediting gate for both:

- *Exogenous premium* (`federal_ces_premium_usd_per_mwh` / `_by_year`): every
  credited MWh earns the scenario-set premium (`premium_for_year` ×
  `unit_credit_fractions`), entering dispatch offers and the screens through
  `max()`. Answers "what does premium $X do".
- *Endogenous target row* (`federal_ces_target_by_year` sparse knots, edge-held,
  `None` = no row; `federal_ces_acp_usd_per_mwh` the ceiling): the row above,
  whose dual is the federal EAC price. Answers "what does an X %-by-Y standard
  imply". `__post_init__` refuses the row in backcast, without the master gate,
  beside a non-zero premium, without a positive ACP, with
  `federal_ces_storage_eligible`, or with wind/solar missing from the eligible
  list. The target schedule is a scenario level (owner box D-2); the SCN-WS2a
  probe's `{2026: 0.55, 2035: 0.80, 2050: 1.0}` / $50 is illustrative.

Postures: state rows + federal row (default when both exist — separate attributes,
`max()` at the screens); `federal_ces_replaces_state_rps=True` (federal row alone —
the flag removes the state RPS **and** state clean rows, never the federal row);
state rows only (REF).

### Voluntary clean-energy demand row (`voluntary_demand.py`) — the family's second consumer

The scenario axis owner ruling **S1** (2026-09-06, card D-3) admitted: a declared,
forecast-only, publicly-anchored, **default-off** what-if over the ffr-5b null (design
memo `docs/handoffs/voluntary-clean-demand-design-memo-2026-09-05.md`; build
`docs/handoffs/FINDING-scn-ws3b-2026-09-06.md`). ONE annual volumetric
clean-attribute row per ISO-year, appended **last** to the family (region order
state → federal → voluntary) through `append_voluntary_region` from the runner's one
resolver `_clean_region_arrays_for_year`, which now takes the year's `zone_demand`:

| Region | Producer | Mask / RHS | Qualifying spec | Escape |
|---|---|---|---|---|
| **Voluntary** (`voluntary_clean_demand_path` ≠ `off`, any ISO) | `append_voluntary_region` | every zone / the uniform share `V / E_total` of every zone's annual demand, so `Σ_z frac·D_z = V` exactly | fuel-name tuple = `voluntary_eligible_fuels` or `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT` (wind, solar, offshore wind, geothermal — the memo §4.1 **recommendation**; owner box D-3c OPEN) | the buyer's willingness-to-pay ceiling: `voluntary_wtp_ceiling_usd_per_mwh` or `VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]` |

**Volume (memo §3.1), DC-linked and read from the run's own demand:**
`V = s_base(path, y) · w_ISO · E_nonDC + f_commit(path, y) · E_DC`, with `E_DC` the
data-centre block's energy (`data.datacenter.datacenter_block_energy_mwh`) and
`E_nonDC = E_total − E_DC`, both taken from the `(n_zones, T)` demand the LP is handed
after `add_load_layers` — a high-DC case raises `V` without a second knob and the
growth×DC relocation is never double-counted. Levels are the cited
`constants.VOLUNTARY_*` tables (NREL national voluntary share 2023 ≈ 0.08 held flat;
`f_commit` low 0 / high 1.0; WTP low 2 / high 7 $/MWh from the cited public REC range);
`f_commit` **mid** and the WTP-ceiling **mid** level are labelled ILLUSTRATIVE
(owner-set under D-2, unreached by S3), and the per-ISO weight `w_ISO` is
`needs-intake` (EIA-861 commercial share; resolves to 1.0). The dual is the voluntary
REC/PPA attribute price — `0` slack, `(0, w]` binding, `= w` when the escape fires and
the shortfall `V − Σ eligible` is the un-procured volume — delivered through the same
`clean_credit_by_fuel → max()` seam as every other region (each eligible fuel at
`dual × 1.0` over the all-zone mask). Trivial-first tests
(`tests/unit/policy/test_voluntary_demand.py`): binding dual = the clean-minus-dirty
cost gap; ceiling dual = WTP with the objective rising by exactly `w × escape`;
curtailed wind is recovered before thermal is displaced.

Guards: `__post_init__` validates the path label and **coerces the whole
`voluntary_*` block to its dataclass defaults in `mode="backcast"` or a hindcast**
(the `datacenter_load_path` construction; `validate_voluntary_config` is the
standalone defense in depth), refuses a non-positive ceiling, a ceiling or eligible
list with the path `off` (a dangling knob, rule 24), and an eligible list without
wind and solar (the family's zone columns credit at 1.0 regardless). Not suppressed by
`federal_ces_replaces_state_rps`. All three fields are cache-optional at their inert
defaults: every keeper key and every committed forecast key is byte-identical at
`off`. Deliberately NOT built: an additionality mask in dispatch, any netting logic
against the federal target row (owner box D-6 OPEN — the campaign reports both
nettings at the report layer; in dispatch the two rows are independent constraints,
FFR-6B §6.4), and an hourly (24/7) row (D-3b: the isolated `scope2-lce-portfolio`
tool). The campaign cases `VOL-MID` / `VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN` are
expressible and **held under owner ruling S5** (Stage A-POLICY).

## 5.3 Carbon pricing (`carbon.py`, `cap_and_trade.py`)

All carbon paths route through one `emission_rate · membership` channel, resolved
by `cap_and_trade.py::resolve_carbon_program(config, year)`. It returns a per-zone
membership `m_zone` plus **exactly one** price source (invariant-asserted):
- **adder path** — an exogenous `$/tCO2` price folded into MC (price known
  ex-ante), or
- **row path** — a `MassCapSpec` whose LP dual is the endogenous allowance price
  (see §5.8).

The two-source split is deliberate: RGGI/CARB are banked, multi-sector markets
this power model does not contain, so their faithful representation is the
exogenous adder; the endogenous row dual is a **power-sector, no-bank scenario**
price (EPA 111(d)/CSAPR or a user cap), never fitted to the observed $/ton.

`CAP_AND_TRADE_PROGRAMS` (`constants.py`, cited) maps ISO→program: CAISO→CARB,
NYISO→RGGI(NY), NEISO→RGGI(6 NE states) with `m_zone≡1` on load zones (import
nodes = 0); PJM→RGGI with a fractional `PJM_RGGI_ZONE_SHARE` (empty → adder ships
OFF pending the EIA-860→state crosswalk); ERCOT/MISO have no program.

`resolve_carbon_price(config, year)` is a thin scalar wrapper over the resolver's
`.price_adder`, resolving by priority:
1. flat `config.carbon_price` if non-zero;
2. else the program adder — **measured** CARB/RGGI auction settlements (2023–2025)
   in backcast, or the **projected** program price in forecast (last realized
   clearing price escalated at the published CARB 5%+CPI / RGGI CCR 7%/yr
   floor-band rate; `CARB_FLOOR_ESCALATION` / `RGGI_RESERVE_ESCALATION`). This
   closes the EM-6 seam — forecast carbon is no longer zero for a program ISO. An
   explicit non-default `config.carbon_price_path` still wins.
3. else interpolate the named `config.carbon_price_path` trajectory;
4. else 0.

The adder enters the dispatch objective as `carbon_price · emission_rate ·
generation` added to each thermal unit's MC (`assemble_mc`, which also accepts a
membership-weighted per-generator adder for a fractional-footprint program). CAISO
unspecified imports carry a border-carbon adjustment (`CARB_UNSPECIFIED_IMPORT_EF
= 0.428 tCO2e/MWh`).

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

`get_active_policy_constraints(config, year)` returns the active constraint-type
policy specs. It surfaces the emissions **mass-cap** spec (§5.8) from the carbon
resolver — `[cap_spec]` when `mass_cap_enabled` and a power-sector budget is
configured, else `[]` — and nothing else (G-S6: the module docstring once named
RPS; it never assembled it). Still the wiring point for future NOx caps and
similar system-wide constraints. The RPS, clean-tier and federal CES target rows
are wired directly by the runner into `model/lp/rows.py` (§5.2), not here.

## 5.8 Emissions mass-cap / cap-and-trade row (`dispatch.py`)

`_build_mass_cap_rows` (GATED, `mass_cap_enabled` default OFF) adds one inequality
row per active power-sector cap:

```
Σ_{g ∈ members} Σ_t  m[g] · emission_rate[g] · P[g,t]  ≤  cap_tons
```

Vectorized (COO block cloned from the RPS row — no hour loop, rule 2). Import-node
and inter-zone flow columns get a **zero** coefficient — the cap is on in-region
emissions, so imported energy's emissions occur outside the capped region; the
leakage channel (a cap raises in-region price → pulls in uncapped imports up to
the transmission limit) is thereby represented, not suppressed.

The row block is appended after the import-node rows and immediately **before** the
RPS row, so the end-anchored dual layout is `[ … | mass_cap (k) | rps (0/1) |
reserve (n) ]` and RPS's distance from the end is unchanged. The mass-cap dual is
recovered end-anchored and reported as `DispatchResult.co2_cap_price = −λ` (one per
cap). This dual is the endogenous allowance price — a **power-sector, no-bank
scenario** price (an upper bound on a banked price in a tight year, ~0 in a loose
year), never a point forecast of the RGGI/CARB market price. No banking/borrowing
across years (each year's cap is enforced independently; the runner's sequential
one-pass year loop and rule 9 forbid the multi-year coupling a true bank needs).

The runner builds the per-generator coefficient `m_zone[zone_idx]·emission_rate`
from each `MassCapSpec` and threads it into the dispatch builder alongside
`rps_target`. `_power_sector_cap` sources the row's `cap_tons` (metric tonnes) in
precedence order: an explicit `config.mass_cap_tons` scenario budget, else the
program's **published** schedule for the year — the cited CARB / RGGI budgets now
landed in `constants.py` (`CARB_ALLOWANCE_BUDGET`, MMT CO2e × 1e6; the regional
`RGGI_STATE_CO2_BUDGET["RGGI"]`, short tons × `SHORT_TON_TO_METRIC_TONNE`), mirrored
by the cited raw schedules under `data/raw/policy/{carb-cap-schedule,rggi-co2-budgets}/`
(curated to the gitignored `data/clean/` via `scripts/data/curate_*.py`). Because those
region-/economy-wide budgets vastly exceed any single modeled ISO's power-sector
emissions, the row is (correctly) **slack** and its dual ≈ 0 for a real ISO — the
mechanism is validated on the trivial binding fixture
(`tests/test_dispatch.py::TestMassCapConstraint`), not by binding against the real
cap. No 2022/2026 budget rows are landed (holdout quarantine, rule 22), so those
years leave the row inert (adder path). Design:
`docs/handoffs/emissions-mass-cap-plan-2026-07.md`.

**The budget schedule (SCN-CAP, owner ruling S12 2026-09-06).** A third, first-ranked
budget source sits ahead of the scalar: `config.mass_cap_tons_by_year`, a
`{ISO: {year: metric tonnes}}` schedule read by `cap_and_trade.scheduled_power_sector_budget`
— sparse knots interpolated linearly between years and edge-held outside them (the last
knot holds flat after 2050; YAML/JSON string keys coerced back to int), `None` for an ISO the
schedule does not name so the scalar → published → inert order below it is untouched. It
exists because a *declining* cap had no expression: `mass_cap_tons` is one number for every
year, and after 2025 the published RGGI path falls back to the eleven-state regional total,
wildly slack for any one ISO (`FINDING-scn-ws1a-2026-09-05.md` §4.1). The precedence is
therefore **schedule → scalar → published → inert**, one composition point (rule 19). The
field is forecast-only: `__post_init__` coerces it to `None` in backcast/hindcast (rule 13),
and it is cache-optional at `None`, so every backcast keeper and every committed forecast key
is byte-identical. The levels are the owner's (rule 1) and live only in the campaign case
`configs/scenario_campaign_matrix.yaml::CAP-STATE-TIGHT` — WS-1a §4.2's linear decline to 20 %
of the 2025 per-state budget by 2050 on CAISO/NYISO/NEISO, CAISO anchored to the model's own
REF-2026 CO2 because CARB publishes no power-sector budget. Read-out and binding table:
`docs/handoffs/FINDING-scn-cap-2026-09-06.md`.

**Row-path boundary (documented limitation).** On the row path the scalar
wrapper `resolve_carbon_price` returns the trajectory fallback (0 by default) —
the cap row carries the carbon cost, so member MC must not also carry an adder
(no double-count). Consequently the CAISO WECC border-carbon adder and the
capacity-evolution screens, which consume that scalar, see no allowance price
under a row-path scenario: the endogenous dual only exists *after* the solve, so
a one-pass build cannot price imports or entry/retirement off it ex-ante (the
plan-§4 aspiration that the border adder "tracks the dual" is not realizable in
this architecture). Row-path CAISO scenarios therefore understate the import
leakage *price* (leakage *volume* via zero-coefficient imports is still
represented); scenario analyses that need a priced border should use the adder
path.
</content>
