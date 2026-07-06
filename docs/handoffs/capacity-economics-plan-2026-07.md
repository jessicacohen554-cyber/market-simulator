# Capacity-Economics Recalibration Plan — 2026-07 (W0-P5)

**Status:** design complete. **W2-P3 Stage 1 (FOM + joint protocol) EXECUTED 2026-07-05 —
see the Stage-1 status note below.** Foresight (§2), floor accreditation (§3), and the DC-load
block (§4) remain for later stages. Implementation prompt in §9.

> ### Stage-1 status note (2026-07-05, W2-P3)
>
> The joint FOM+scarcity protocol (§5) ran the full 2×3 ERCOT + 2-cell PJM probe matrix
> (`scripts/run_fom_scarcity_grid.py`; report `docs/handoffs/fom-scarcity-joint-protocol-2026-07-05.md`
> + `fom-scarcity-grid-2026-07-05.json`). **Decision: the ATB FOM defaults were NOT flipped.**
> The grid showed the going-forward FOM level is currently **inert** in the ERCOT forecast — the
> nameplate reliability floor retains 100 % of thermal (floor ≈100 GW > ~72 GW fleet) and the
> adequacy backstop backfills the rest, so CT 8→21 / CC 12→30 / coal 40→45 moves **zero MW and
> zero CO₂** (capacity trajectory byte-identical across the FOM axis). The revenue side is also
> understated vs the Potomac ERCOT SOM observable (fleet CT ≈1.5 vs SOM ≈68 $/kW-yr). Per rule 1
> ("judge by structure, not residual") the recalibration is **blocked behind two prerequisites,
> both later stages**: **(A) the §3 floor-accreditation redesign** (so the floor stops masking the
> economic screen — the dominant blocker) and **(B) the §5-step-2 revenue-side fix** (published
> ORDC params / endogenous co-opt). The ATB values (21/30/45) are recorded as the frozen,
> externally-identified targets (DOF ledger in the report); the current mis-citation in
> `parameters.json` ("NREL ATB 2024" for values that are actually sub-ATB avoidable estimates) was
> corrected. **Landed this session:** the pure-diagnostic screen-revenue log in
> `apply_economic_retirements`, `run_fom_scarcity_grid.py`, the `TestFomThresholdFlip` behavioural
> test, the protocol report + grid JSON, and the citation correction. **Deferred with the flip:**
> the tornado FOM-band re-centring + `fom_and_scarcity` paired perturbation (re-centring bands on
> defaults that have not moved would misreport the base case). No CAISO change (collision with the
> live scalar remediation). No 2022/H1-2026 solve.

> ### Stage-1 reconciliation note (2026-07-05, PR #1413 rebase)
>
> The implementation leg of this workstream — **the §3 floor-accreditation redesign
> (prerequisite A above), the §2.3 entering-year known-peak substitution, the §2.2/§2.3
> EWMA + lookahead price-signal stack (default off), the foresight A/B harness, and the
> joint FOM+scarcity grid + revenue-side audit harnesses** — landed via PR #1413, rebased
> onto and reconciled with the already-merged Stage-1 decision leg (#1417) and the
> intervening merges #1414 (announced-retirements rename + confirmed-exits channel),
> #1410/#1415 (evolution-ledger out-params), and #1416 (forecast-path AS admissibility
> guard). Two facts about the original decision text above are reconciled here **without
> rewriting it** (the decision stands):
>
> 1. **The "nameplate reliability floor" that made FOM inert is now replaced.** The §3
>    rebuild retires the raw-nameplate floor (`(peak − hydro) × 1.15`) in favour of the
>    accredited-basis floor (`accredited_firm_capacity_mw` UCAP/ELCC vs
>    `peak × (1 + PLANNING_RESERVE_MARGIN_BY_ISO)`), with the CO₂-aware retention tie-break
>    and the `floor_retention_log` attribution. So the specific mechanism the decision cited
>    ("nameplate floor ≈100 GW > ~72 GW fleet retains 100 % of thermal") no longer exists as
>    described — its dominant-blocker (A) is now implemented.
> 2. **The ATB FOM defaults remain UNFLIPPED (CT 8 / CC 12 / coal 40).** Landing the floor
>    mechanism does **not** by itself license the flip: per plan §5.4 the flip is gated on a
>    **re-run of the §5 grid against the new accredited floor** (to establish whether FOM is
>    still inert or now moves MW/CO₂) **and** prerequisite B (the revenue-side ORDC/co-opt
>    fix). Neither the grid re-run nor the tornado FOM-band re-centring is performed in this
>    landing — they are forecast probes, not required to land the mechanism, and re-centring
>    bands on unmoved defaults would still misreport the base case (rule 1). The
>    `fom-scarcity-grid-2026-07-05.json` numbers and the fom-scarcity-joint-protocol report's
>    §2.1/§4 "FOM is inert" tables were produced against the **old nameplate floor** and are
>    now **stale for the accredited floor**; they remain valid as the record of the Stage-1
>    decision but must be regenerated before the flip.
> 3. **Foresight A/B artifacts are stale.** The A/B code path (`evolve_fleet` signature, the
>    accredited floor, the entering-year known-peak) changed in this rebase, so any
>    pre-rebase local A/B run is invalid. No A/B results doc/JSON is committed on this branch
>    (only the `run_foresight_ab.py` harness); the harness must be re-run on the reconciled
>    code before its metrics are quoted or any arm is promoted (plan §2.4 decision rule).
>    Re-running is a multi-year forecast solve — deferred, not blocking the landing.

> ### Stage-2 status note (2026-07-05, W2-P3 Stage 2)
>
> The §5-step-2 **revenue-side fix landed**: the retirement screen's margin basis is now
> the attainable pro-forma `max(0, price − mc, reserve price) × pmax × availability`
> (the Potomac-SOM net-revenue construction, matching the entry screen's existing basis),
> and an hourly reserve-price signal (`screen_reserve_value_enabled`, default on — co-opt
> duals under `ercot_thermal_as_endogenous`, else the ORDC adder per RTORPA/RTOFFPA,
> Nodal Protocols §6.5.7.5) is the sole thermal AS pricing when present (rule 19). VRE
> entry is shape-aware (§6 CX-6c: build zone hourly CF × zonal prices). First-screen-year
> ERCOT CT revenue moved 1.5→17.2 $/kW-yr against the SOM ≈68 upper anchor — no
> multiplier closes the rest (rules 1/14/26). The §5.4 grid was re-run against the
> accredited floor (`fom-scarcity-grid-2026-07-05-stage2.json`): **FOM is STILL inert —
> the defaults were again NOT flipped.** The masking is no longer the Stage-1 ledger bug
> but genuine mid-growth adequacy shortage: the accredited floor correctly un-retires
> every eligible unit and the harness-enabled backstop floods CT (15.2 GW in the first
> three years), collapsing scarcity below every bar. Gates fail (pace 0 GW/yr, backstop
> ≫ 0). Tornado FOM re-centring + `fom_and_scarcity` perturbation remain deferred with
> the flip. The foresight A/B re-run (§2.4) remains the open next step — its lookahead
> arm is one of the three unblocking paths recorded in the Stage-2 report §3. Also
> landed: the announced-channel **retirement-reversal supersession** (Byron/Dresden CEJA
> rows seeded; see `confirmed-retirement-plan-2026-07.md` §4.3.2) and the ERCOT realized
> capacity-hindcast re-run registered as the before/after diagnostic on the
> forecast-validation dashboard. Full report:
> `docs/handoffs/fom-scarcity-joint-protocol-2026-07-05-stage2.md`.

**Inputs:** `docs/fable-repo-audit-2026-07.md` §C (CX-1…CX-6), CLAUDE.md rules 1, 5, 10, 13,
14, 19, 21, 22, 24, `docs/fable-prompt-pack-2026-07.md` W0-P5/W2-P3,
`docs/forecast-methodology-gaps-2026-06.md` (scarcity/AS revenue understatement),
`docs/model-audit-2026-06.md` (exogenous AS overlay), `docs/handoffs/sensitivity-tornado-ercot-2026-07-04.md`.
**Everything here is LP-only**: pre-solve signal construction, screen arithmetic, and config
plumbing. No MIP, no within-year iteration (one-pass rule 10 preserved throughout).

---

## 0. SCOPE GUARD — which "reliability floor" this plan touches

This plan concerns **only** the capacity-evolution retirement floor inside
`apply_economic_retirements` (`src/market_sim/model/capacity.py:573-589`; audit anchor
"553-569" predates line drift): the `(peak − firm_clean) × (1 + retirement_reserve_margin)`
thermal-retention rule in the **annual retirement screen**, plus its siblings in the same
annual capacity-evolution layer (`apply_reserve_margin_build`, `apply_economic_new_entry`).

It must **NOT** touch, weaken, or remove the **dispatch-layer** temperature-dependent
reliability floors — `src/market_sim/data/floor_mechanisms.py` and the CAISO/NEISO
temperature limbs in `src/market_sim/model/transmission.py`. Those are an *hourly commitment*
mechanism with their own drivers, windows, and forward stories (rules 17–20); they are a
separate phenomenon and stay in, unchanged. Any W2-P3 diff that modifies those files for
floor semantics is out of scope by definition.

## 0.1 Current-state map (verified 2026-07-05, line numbers current)

| Mechanism | Where | Today's behaviour |
|---|---|---|
| Going-forward FOM bars | `config/scenarios.py:195-211` (`fixed_om_gas_ct=8`, `fixed_om_gas_cc=12`, `fixed_om_coal=40` ×1.3 multiplier = 52 effective, `fixed_om_gas_st=35`, `fixed_om_oil=25`, `fixed_om_nuclear=130`) | Retirement screen bar (`capacity.py:556-559`) |
| Retirement screen revenue stack | `capacity.py:479-567` | Inframarginal energy margin + attribute (EAC/RPS max) + capacity payment (net-CONE × UCAP, non-ERCOT) + AS credit (ERCOT exogenous or co-opt-derived) |
| Retirement reliability floor | `capacity.py:573-589` | Raw thermal **nameplate** vs `(peak − hydro) × 1.15`; un-retires lowest-heat-rate eligible units; no logging; non-locational |
| Accredited firm capacity | `capacity.py:1315-1341` (`accredited_firm_capacity_mw`) | UCAP/ELCC accounting — used by the step-6 build backstop, **not** by the floor |
| Reserve-margin build backstop | `capacity.py` `apply_reserve_margin_build` / `evolve_fleet` step 6 (`capacity.py:1762-1793`) | Force-builds gas_ct to `PLANNING_RESERVE_MARGIN_BY_ISO` on the **accredited** basis vs **prior-year** peak |
| Price signal for all screens | `runner.py:1240-1291` (`econ_prices` = prior-year LP duals + post-solve ORDC adder on ERCOT), threaded via `prior_results` into `evolve_fleet` (`capacity.py:1655-1660`) | Pure one-year myopia: year Y screens see only year Y−1 outcomes |
| Demand | `runner.py:190-205` (`_scale_demand`), `constants.py:690-726` (`DEMAND_GROWTH_RATES`, near/long eras, transition 2030) | One uniform scalar on the frozen weather-year hourly shape; DC + electrification implicitly buried in the near-term rates |
| Nuclear RPS | `dispatch.py:372-392` (`_build_rps_row`: wind+solar+**nuclear** columns), `capacity.py:100` (`_CLEAN_FUELS` incl. nuclear/hydro gets RPS shadow in retirement screen) | CX-6a |
| WACC | `scenarios.py` `nominal_discount_rate=0.08` → `real_discount_rate` property (`scenarios.py:3213-3218`) | One rate for every tech (CX-6b) |
| VRE entry revenue | `capacity.py:1263-1276` (`estimate_expected_revenue(prices, base_cf)` with **scalar** cf) | Shape-blind flat-mean price (CX-6c); the function already accepts hourly cf arrays (`capacity.py:937-965`) |

---

## 1. Item 1 (CX-1) — Going-forward FOM recalibration

### 1.1 The problem, stated precisely

The retirement bar is `FOM_field × multiplier × pmax`. Current defaults (ct 8 / cc 12 /
coal 40×1.3=52 $/kW-yr) sit ~1.5–2.5× below the reference-cost literature for *existing-unit
ongoing* fixed cost (NREL ATB 2024: CT ≈ 21, CC ≈ 30 $/kW-yr; existing coal per EIA/Sargent &
Lundy ≈ 40–60). A bar that low means a fossil unit covers "fixed cost" with a fraction of
real-world net revenue → systematic under-retirement → forecast emissions biased high.

One nuance keeps this from being a naive swap: the *economically correct* bar is the
**avoidable going-forward cost** (what exiting saves), which is a subset of accounting FOM —
the PJM Avoidable Cost Rate (ACR) concept. ATB FOM is a total-plant ongoing figure and a
defensible *upper* anchor; today's values resemble an aggressive avoidable-only reading with
no citation. The recalibration adopts ATB-class values as the default and keeps today's
values as the documented low band of the sensitivity, not as defaults.

### 1.2 Proposed parameter design (all `ScenarioConfig`, rule 24; citations rule 5)

| Field | Today | Proposed | Citation (into `parameter-citations.md` via `frontend/data/parameters.json`) |
|---|---|---|---|
| `fixed_om_gas_ct` | 8.0 | **21.0** | NREL ATB 2024, Gas CT (F-frame), FOM $/kW-yr; cross-check Brattle ERCOT CONE 2026 frame-CT FOM component |
| `fixed_om_gas_cc` | 12.0 | **30.0** | NREL ATB 2024, Gas CC FOM — **already the repo's cited value for a *new* CC** (`NEW_ENTRY_COSTS["gas_cc"]["fom_per_kw_yr"]=30`, `constants.py`); an existing CC claiming 12 while a new one pays 30 is internally inconsistent |
| `fixed_om_coal` | 40.0 | **45.0** (effective 58.5 with the retained 1.3 coal multiplier) | EIA "Generating Unit Annual Capital and Life Extension Costs" (Sargent & Lundy, 2019/updated) existing-coal FOM $40–60/kW-yr; NREL ATB 2024 coal-FOM class ≈ 45 |
| `fixed_om_gas_st` | 35.0 | keep 35.0 | Already in the ATB/Lazard legacy-steam band (cited inline) — re-verify citation date only |
| `fixed_om_oil` | 25.0 | keep 25.0 | Within EIA O&M band for oil steam/CT; re-verify citation |
| `fixed_om_nuclear` | 130.0 | keep 130.0 | NEI "Nuclear Costs in Context" total generating cost ≈ $120–135/kW-yr avoidable share; already cited |
| `retirement_fom_multiplier_coal` | 1.3 | keep 1.3 | Lazard LCOE 2024 (regulatory/ESG/insurance risk premium) — unchanged; it is a *risk* adder, orthogonal to the FOM level |

Rules of engagement (rule 21 DOF ledger discipline):

- The FOM values are **externally identified and frozen**: they come from ATB/EIA-S&L and may
  only change when those sources update (rule 23 analogue). They are *never* tuned against a
  retirement-pace or emissions residual.
- Do **not** land the new defaults in the same commit that builds the mechanism changes.
  Sequence: (a) wire the joint sensitivity protocol (§5), (b) run its probe matrix and commit
  the results doc, (c) flip the defaults in a dedicated commit citing the probe results.
- `parameters.json` entries: tier 2, source strings exactly as in the table, `modeled` flag
  off (these are measured/published reference costs).

### 1.3 Why FOM cannot move alone — the scarcity coupling

The 2026-06 assessments flag that the model's screens *under-collect* scarcity/AS revenue:
the exogenous ERCOT AS overlay is a calibrated bridge (`model-audit-2026-06.md`
`ERCOT_AS_REVENUE_PER_KW_YR` "calibrated, exogenous"), the endogenous multi-product AS co-opt
is the designated forward mechanism but not yet the default
(`forecast-methodology-gaps-2026-06.md` G1/P1), and the perfect-foresight LP produces zero
unserved energy, so absent the post-solve ORDC adder (`runner.py:1240-1286`, ERCOT-only) the
energy margin carries no scarcity rent at all. Raising FOM ~2× against an understated revenue
stack over-retires exactly the way today's low FOM under-retires — the two errors currently
*cancel by accident*. Per rule 1 the fix is to correct both sides on their own evidence, not
to keep the cancellation. §5 is the joint protocol that enforces this.

### 1.4 Expected emissions direction

Fossil retirement accelerates, concentrated where net revenue is thinnest (old coal, gas
steam, low-CF CTs). Forecast CO₂ **down**, largest in the 2030s once the loss-year counters
bite. Failure mode to watch: over-retirement pushing the reserve-margin backstop
(`apply_reserve_margin_build`) into large forced gas_ct builds — that substitutes emissions
(CT for coal, still down) but signals the scarcity side is still understated (§5 acceptance
gates).

---

## 2. Item 2 (CX-2) — One-pass myopia vs steep load growth

### 2.1 The problem

Every screen in year Y consumes only year Y−1 prices/dispatch (`runner.py:1288-1291` →
`capacity.py:1655-1660`). Under ERCOT-mid 5%/yr near-term growth, entry perpetually chases a
demand level that has already moved, incumbent fossil fills the gap, and the fleet lags the
ramp for the whole near era — biasing 2026-2035 fossil dispatch and emissions high. Two
candidate fixes, both **pre-solve signal construction** (the LP and the one-pass loop are
untouched; rule 10 intact):

### 2.2 Candidate A — EWMA price-signal blend (anti-whipsaw, not anti-lag)

`signal_Y = α · econ_prices_{Y-1} + (1−α) · signal_{Y-1}` threaded through `prior_results`
as a new key (`price_signal`), consumed by the retirement/entry/storage screens in place of
raw `prices`. New field `entry_price_signal_alpha: float = 1.0` (α=1.0 ⇒ byte-identical
today's behaviour; probe value 0.6).

Honest characterization: EWMA looks *backward* — it does not fix growth lag, it fixes
single-draw whipsaw (one weather/outage-shaped year triggering a retirement or entry wave the
next year reverses). It is the right tool for CX-5-adjacent transient-dip over-retirement,
and mildly *worsens* lag under monotone growth. It earns its A/B slot as the control arm that
separates "noise smoothing" from "foresight" effects.

### 2.3 Candidate B — growth-scaled lookahead via stack re-pricing (the real fix)

Two admissible components, both regenerating from forward drivers (rule 13: the demand path
is exogenous config, the supply stack is the model's own state — both exist in any forecast
year and respond to changed conditions):

1. **Known-demand substitution in peak-anchored mechanisms.** The retirement floor and the
   reserve-margin backstop currently test against *prior-year* `peak_demand`
   (`capacity.py:1658`, `1767`). Year Y's demand is deterministically known
   (`_scale_demand`); thread `peak_demand_next = year_demand_Y.sum(axis=0).max()` computed
   *before* `evolve_fleet` and use it in both. Zero new parameters; removes one full year of
   pure bookkeeping lag. (This is not foresight — it is deleting an off-by-one.)
2. **Stack re-price of the entry/retirement price signal.** Re-price the prior year's
   marginal-cost supply stack against year Y's known net-load duration:
   `net_load_Y[t] = demand_Y[t] − renewables_{Y-1}[t]` (prior-year VRE output, since builds
   aren't known yet); sort the prior fleet's `(mc, available_capacity)` stack once; price
   each hour by `np.searchsorted` of `net_load_Y` into cumulative capacity; where the stack
   exhausts, apply the same ORDC scarcity curve the runner already uses
   (`results.scarcity.scarcity_prices`). O(T·log G) numpy, no LP, no loop over hours
   (rule 2). Gate: `entry_lookahead_reprice: bool = False`. This is the pro-forma a real
   developer runs — projected load against the known fleet — with **zero fitted
   parameters**: every input is an existing model quantity.

   Guardrail: the re-priced signal feeds **only** the capacity screens
   (entry/retirement/storage), never dispatch, never results, never the backcast (backcast
   mode has no capacity evolution, so it is structurally unreachable there).

### 2.4 The A/B foresight experiment (decides what W2-P3 promotes)

- **Setup:** ERCOT, forecast 2026-2040, `demand_growth_path="high"` (8%/yr near / 4% long —
  the stress case where myopia is maximal), plus a mid-growth replicate to check the
  conclusion isn't stress-case-only. Legacy bin fleet (`use_campd_bins=False`) for runtime,
  matching the tornado's documented fidelity trade (`run_sensitivity_tornado.py` header);
  sequential years, ≤2 concurrent invocations (rule 12).
- **Arms (4):** (0) base myopic; (1) EWMA α=0.6; (2) lookahead = known-demand substitution +
  stack re-price; (3) both.
- **Metrics, 2030-2040 window:** fossil dispatch TWh by class (coal / gas_cc / gas_ct+st),
  cumulative CO₂ Mt, cumulative retirements GW, cumulative economic entry GW by tech,
  reserve-margin-backstop forced MW by year (the myopia tell: a chronically-firing backstop
  is the fleet lagging), mean and P95 annual price.
- **Materiality bar:** an arm is *material* if 2030-2040 cumulative fossil CO₂ moves >5% vs
  arm 0, and *preferred* if it also reduces backstop forced-build MW (evidence the economics,
  not the backstop, are building the fleet).
- **Decision rule:** promote the simplest material arm. Expected outcome: (2) material,
  (1) not (or price-volatility-only); component 1 of arm 2 (known-demand substitution) is
  promoted **unconditionally** — it is a bug-class fix, not a mechanism choice. If nothing is
  material, keep component 1, document myopia as a measured-immaterial limitation, and leave
  `entry_lookahead_reprice` default-off as a designed probe.
- All arms are forecast probes: **no dashboard registration** (dashboard is backcast-only),
  results go in a `docs/handoffs/foresight-ab-ercot-2026-*.md` report + JSON, tornado-style.

### 2.5 Expected emissions direction

Lookahead pulls entry (mostly solar/wind/CT/storage under current cost paths) earlier, so
incumbent coal/gas fills less of the growth gap: 2030s fossil dispatch and CO₂ **down**.
EWMA alone: direction ambiguous, magnitude small (smooths transient retire/re-enter cycles).

---

## 3. Item 3 (CX-3) — Retirement reliability floor: accreditation, tie-break, attribution

### 3.1 Defects in the current floor (`capacity.py:573-589`)

1. **Wrong accounting basis.** It sums retained **raw thermal nameplate** against
   `(peak − hydro_nameplate) × (1 + retirement_reserve_margin)`. Nameplate ≠ firm: an 8%-EFORd
   coal unit counts at 100%, wind/solar/storage count at 0% (they're netted out only via the
   hydro-only `_FIRM_CLEAN_FUELS`). The codebase already owns the correct accounting —
   `accredited_firm_capacity_mw` (`capacity.py:1315`, UCAP = 1−EFORd for thermal,
   `RENEWABLE_CAPACITY_CREDIT` for VRE, duration-ELCC for storage) — and the step-6 build
   backstop already uses it. Floor and backstop currently answer the same adequacy question
   with two different ledgers (rule 19 violation in spirit).
2. **Emission-blind retention.** Un-retirement keeps the lowest-heat-rate eligible units.
   Heat rate is a *cost* proxy, not a *firmness or emissions* one: a 10.2 mmBtu/MWh coal unit
   outranks an 11.0 CT, so the floor can non-economically retain coal over gas while both
   satisfy adequacy identically per MW.
3. **No attribution.** A unit kept by the floor is indistinguishable from one that earned its
   keep. Nothing logs floor retention, so floor-vs-economic attribution (the D-2 discipline
   rules 19-20 demand for dispatch floors) is impossible for the capacity layer, and the
   tornado's `retired_thermal_gw` conflates the two.
4. **Non-locational.** One system-wide test; a load pocket can be stripped while a long zone
   hoards retained capacity.

### 3.2 Redesign

Replace the floor block with:

```
requirement_mw   = peak_demand_used × (1 + PRM_iso)          # PLANNING_RESERVE_MARGIN_BY_ISO,
                                                             # same constant the backstop uses;
                                                             # retirement_reserve_margin is DELETED
                                                             # (rule 26: not zeroed — removed)
accredited_after = accredited_firm_capacity_mw(survivors, wind_pool, solar_pool, storage_firm)
while accredited_after < requirement_mw and eligible remain:
    un-retire next unit by retention merit; accredited_after += pmax × (1 − EFORd)
```

- `peak_demand_used` = current-year known peak if item-2 component 1 lands, else prior-year
  (the two changes compose but don't depend on each other).
- `wind_pool/solar_pool/storage_firm` already ride `prior_results`
  (`wind_cap_mw`/`solar_cap_mw`/`storage_firm_mw`, `runner.py:1338-1339`); thread them into
  `apply_economic_retirements` as new optional args (default 0.0 ⇒ conservative floor,
  backward compatible for tests).
- **Retention merit (emission-aware tie-break):** sort eligible units by
  `going_forward_cost / (pmax × (1 − EFORd))` ascending ($/firm-MW-yr — cheapest adequacy
  first), tie-broken by `emission_rate_co2` ascending. Cost stays the primary key (the floor
  is an adequacy purchase, and a cost-blind emissions key would buy expensive adequacy);
  the CO₂ key breaks the coal-vs-gas ties the heat-rate key currently gets backwards. Both
  keys are physical unit attributes — no new tunables.
- **One requirement, two verbs (rule 19 reconciliation):** the floor (don't retire below the
  requirement) and the step-6 backstop (build up to the requirement) now share one accounting
  basis (`accredited_firm_capacity_mw`) and one margin constant (`PLANNING_RESERVE_MARGIN_BY_ISO`).
  `retirement_reserve_margin` (0.15, uncited, separate from the backstop's PRM) is removed
  from `ScenarioConfig`; its tornado entry (`reserve_margin`) re-points at the PRM table.
- **Attribution logging:** every floor retention appends
  `{year, unit_id, fuel_type, pmax_mw, ucap_mw, going_forward_cost, co2_rate, loss_years}`
  to a `floor_retention_log` returned through `evolve_fleet` (alongside `retrofit_log`) and
  persisted next to the per-year results parquet (`floor_retentions.json`). Acceptance
  analogue of rule 20: a forecast run report must state floor-retained MW as a share of
  surviving thermal; a mechanism change that grows this share is masking an economics bug,
  not fixing adequacy.
- **Locational:** deferred. The honest locational version needs the deliverability part-(b)
  machinery (zonal requirements, `deliverability_headroom_by_zone`) which is built but
  unvalidated in any keeper (CLAUDE.md capacity section). Design note: when
  `capacity_deliverability_limits` is on, the floor should exempt RA-saturated zones from
  retention (mirror of the screens' `_zone_is_long` gate) — implement behind that same flag
  in W2-P3 **only if** its tests are cheap; otherwise document as the flag's known remaining
  gap. Non-locational stays the default either way.

### 3.3 Expected emissions direction

Two opposing pushes, both correct: (a) counting VRE/storage capacity credit toward the
requirement means the floor binds **less** often → more coal/steam actually retires → CO₂
down; (b) UCAP-discounting thermal (−5…−8%) tightens the requirement slightly → floor binds
more in thermal-heavy years → CO₂ up marginally. Net expected: **down**, because (a)
dominates in every ISO with nontrivial VRE, and when the floor does bind the CO₂ tie-break
retains gas ahead of coal (down again). Attribution logging makes the direction *measurable
per run* rather than argued.

---

## 4. Item 4 (CX-4) — Data-center block + electrification shape adder

### 4.1 The problem

`_scale_demand` applies one compound scalar to a frozen weather-year hourly shape
(`runner.py:190-205`); `DEMAND_GROWTH_RATES` buries the DC boom inside near-term rates
(`constants.py:686-726`, "elevated by data center"). Consequences: (a) DC load — flat,
~0.85+ load factor — is grown with the *system's* peaky shape, overstating peak growth and
understating energy growth per MW of DC; (b) the DC path cannot be varied independently of
organic growth (the single most-asked scenario question); (c) electrification (heat pumps,
EVs) reshapes hours, which a scalar cannot represent.

### 4.2 Design — additive flat block, separately parameterized

**ScenarioConfig (rule 24, all in `run_config.json`):**

```python
datacenter_load_path: str = "off"        # "off" | "low" | "mid" | "high" — selects the
                                         # per-ISO cumulative-MW trajectory from constants.
                                         # "off" = today's behaviour, byte-identical.
datacenter_load_factor: float = 0.85     # flat hourly CF of the block.
                                         # Source: LBNL 2024 United States Data Center Energy
                                         # Usage Report (large-DC utilization); EPRI 2024
                                         # "Powering Intelligence" load-factor range 0.8-0.95.
datacenter_percentile: float = 0.5       # PB-1-style continuous lever across low/mid/high,
                                         # mirroring demand_growth_percentile.
```

**constants.py:**

```python
DATACENTER_ADDITIONS_MW: dict[str, dict[str, dict[int, float]]]
# {iso: {path: {year: cumulative MW}}}, piecewise-linear between anchor years, flat after
# the last anchor. Anchors and citations per ISO:
#   ERCOT — ERCOT 2025 Long-Term Load Forecast, large-flexible-load (LFL) officer update:
#           interconnection-agreement-backed MW by year (use the contracted subset for
#           mid, officer high case for high, signed-only for low).
#   PJM   — PJM 2025 Load Forecast Report, data-center component of the 15-yr forecast
#           (PJM publishes the decomposition explicitly).
#   MISO/NYISO/NEISO/CAISO — ISO load-forecast DC line items where published (NYISO Gold
#           Book large-load adjustments, CAISO IEPR data-center adder); low path = 0 where
#           no published decomposition exists (do NOT invent one; needs-citation flags
#           forbidden here — a path with no source ships as 0).
DATACENTER_ZONE_SHARE: dict[str, dict[str, float]]
# {iso: {zone: share}} summing to 1.0. Default: the ISO's zonal load_share. Override where
# siting is published (ERCOT: skew to North/Oncor + West per ERCOT LFL queue geography;
# PJM: Dominion zone per PJM forecast). Physical siting data, not a tunable.
```

**Mechanics (runner, after `_scale_demand`):**

```
dc_mw     = interp(DATACENTER_ADDITIONS_MW[iso][path], year)   # percentile-blended like
                                                               # resolve_demand_growth_rate
demand[z] += dc_mw × datacenter_load_factor × DATACENTER_ZONE_SHARE[iso][z]   # flat 8760
```

Peak, energy, and every capacity mechanism downstream pick the block up automatically
through `year_demand` / `peak_demand`. Vectorized broadcast; no hour loop.

**Decomposition discipline — the critical step.** `DEMAND_GROWTH_RATES` near-term mid rates
*currently include* the DC boom. Landing the block without re-deriving organic growth
double-counts. W2-P3 must, in the same change: re-derive `DEMAND_GROWTH_RATES` near-term
entries as **organic-ex-DC** rates such that `organic^new + mid DC block ≈ current mid total
energy at 2030` per ISO (continuity constraint, documented per ISO in the constants comment
and `parameter-citations.md`, citing the same sources' ex-DC decompositions — EIA STEO
ex-data-center electricity growth, the ISO forecast components). The high/low demand paths
then vary organic growth; `datacenter_load_path` varies the block; the PB-1 sampler
(`probability-bounds-plan-2026-07.md` §1.1) gains the DC axis it already anticipated
(prompt-pack W2-P6 note).

**Backcast:** the block is forecast-mode-only by construction (`datacenter_load_path="off"`
default; backcast keepers pin measured load). Add a config validator rejecting
`mode="backcast"` with a non-off DC path.

### 4.3 Electrification shape adder — design sketch, default off, W2-P3-optional

`electrification_shape_path: str = "off"` selecting a per-ISO **additive hourly profile**
(winter-morning/evening heat-pump ridge + EV evening, normalized to 1 TWh) scaled by an
annual TWh trajectory (`ELECTRIFICATION_TWH[iso][path][year]`, NREL Electrification Futures
Study reference/high cases; ISO heating-electrification studies where published). Applied
identically to the DC block (add, don't scale). **Recommendation: ship the config plumbing
and profile loader interface in W2-P3 only if trivially cheap; otherwise document as the
explicit remaining limitation** — the DC block is the material near-term input error
(flat, huge, certain); electrification shape is smaller and later-horizon. Either way the
audit's PP-3.3 "end-use reshaping remains a documented limitation" note carries forward
until the profiles are sourced.

### 4.4 Expected emissions direction

Versus today **at equal total annual energy** (the honest comparison, post-decomposition):
the flat block shifts growth from peak hours into all hours — off-peak/overnight net load
rises, so mid-merit gas_cc (and surviving coal overnight) runs more while peak-hour growth
(scarcity, CT builds) *slows*. Expected: CO₂ **up slightly** per TWh (more energy served by
mid-merit fossil at night in the near term), price shape flattens, scarcity-driven CT/storage
entry signal weakens modestly. Versus a naive "DC added via higher uniform scalar": lower
peak → less over-building of peakers and less phantom scarcity revenue. High-DC path grows
total energy: CO₂ **up** in absolute terms until entry catches up — which is exactly the
item-2 interaction (the two items must land in the same tornado refresh).

---

## 5. Joint FOM + scarcity sensitivity protocol (rule 1: no co-tuning against one residual)

**Threat model.** FOM (cost side) and scarcity/AS revenue (revenue side) hit the retirement
inequality `net_revenue < going_forward_cost` from opposite sides. Tuned independently
against the same observable (retirement pace / emissions), they are unidentified — any error
in one can be absorbed by the other, re-creating the current accidental cancellation with
new numbers. The protocol makes each side identified by its **own external evidence** and
uses the joint grid only as *verification*, never calibration.

**Identification (the DOF-ledger entries, rule 21):**

| Side | Parameter(s) | Identification source (NOT the retirement residual) |
|---|---|---|
| Cost | `fixed_om_*` per §1.2 | NREL ATB 2024 / EIA-S&L published values; frozen |
| Revenue | ORDC params (`ordc_voll`, `ordc_lolp_*`), `ERCOT_AS_REVENUE_PER_KW_YR` or the endogenous co-opt | Published ERCOT ORDC methodology + Potomac Economics ERCOT State of the Market **net-revenue tables** (CT and CC $/kW-yr by year) — a measured *validation observable* for the screens' revenue stack, admissible under rule 13 (compare, never pin) |

**Protocol steps (execute in W2-P3 before flipping FOM defaults):**

1. **Revenue-side audit first.** For the ERCOT backcast years 2023-2025 (in-sample; holdouts
   untouched, rule 22), compute the retirement screen's per-class revenue stack (energy
   margin + ORDC adder + AS credit, $/kW-yr for gas_ct and gas_cc) from the existing keeper
   bundles — no new solve needed — and table it against the Potomac SOM net-revenue estimates
   for the same years. Record the ratio per class/year in the protocol report.
2. **Root-cause any shortfall on the revenue side.** If the screen collects materially less
   than SOM (expected per the 2026-06 assessments), the corrective actions are mechanism
   actions — ORDC parameters set from the published methodology, engaging the endogenous
   co-opt path (`ercot_thermal_as_endogenous`) — never an FOM haircut and never a multiplier
   swept against retirement counts (`as_revenue_multiplier` stays 1.0; rule 26 memory: the
   ORDC offset was deleted for exactly this re-arming risk).
3. **The 2×3 verification grid** (six forecast probes, ERCOT 2026-2031, mid growth,
   sequential years, ≤2 concurrent): FOM ∈ {legacy, ATB} × scarcity ∈ {overlay off,
   ORDC overlay (today's default), endogenous co-opt}. Record per cell:
   `retired_thermal_gw` by fuel, backstop forced-build MW, CO₂ path, CT/CC screen revenue
   $/kW-yr. Repeat the FOM axis only (2 cells) on PJM 2026-2031 to verify the capacity-market
   revenue side (net-CONE × UCAP) covers ATB-level FOM for efficient CC — if it doesn't, the
   PJM `net_cone_per_kw_yr` registry value gets re-checked against the published BRA/CONE
   filing (again: fix the revenue input at its source, don't bend FOM).
4. **Acceptance gates for flipping the defaults:**
   - ATB-FOM × default-scarcity cell: near-term (2026-2028) retirement pace within the
     observed ERCOT range (~0.5–2 GW/yr thermal) and backstop force-builds ≈ 0 in the first
     three years. Backstop firing at scale = revenue side still broken = **stop**, root-cause
     per step 2; do not revert FOM (rule 14 logic: the accurate input stays, the compensating
     error gets fixed).
   - The FOM tornado entries (`fixed_om_coal/gas_cc/gas_ct` already in
     `run_sensitivity_tornado.py`) re-run with bands re-centered on the new defaults
     (low = legacy value, high = ATB × 1.25 per S&L age escalation), and **one new paired
     perturbation** (`fom_and_scarcity`, both axes moved together) is added so the
     interaction term (non-additivity of the two single-axis swings) is measured and recorded
     — the quantitative tripwire that would catch future silent co-tuning.
5. **Report:** `docs/handoffs/fom-scarcity-joint-protocol-<date>.md` + JSON, tornado-style;
   the FOM-default-flip commit cites it. Forecast probes only — nothing registers on the
   backcast dashboard; no keeper config changes (current ERCOT keepers don't consume
   `fixed_om_*` — backcast mode has no capacity evolution — so no re-gate is triggered).

---

## 6. CX-6 adjudication

| Sub-item | Verdict | Rationale & design |
|---|---|---|
| **Nuclear RPS eligibility** (`dispatch.py:372-392` RPS row counts nuclear; `capacity.py` `_CLEAN_FUELS` grants nuclear/hydro the RPS shadow in the retirement screen) | **PARTIALLY LANDED — see §6.1 (U-03)**: retirement-screen half fixed (L-7 2026-07-06); `_build_rps_row` half deferred to a dispatch-owning lane | Real RPS programs overwhelmingly exclude existing nuclear (and large hydro); state nuclear support is ZEC-shaped, which the model already carries separately (`eac_price_nuclear` — NY/IL ZEC, `scenarios.py:127`). Counting nuclear in the RPS row suppresses the REC dual toward zero in every year nuclear+VRE already clears the target, killing the entry signal the dual exists to send. Fix: split `_CLEAN_FUELS` into `_RPS_ELIGIBLE_FUELS = {wind, solar}` (RPS row + shadow-price credit) vs the existing clean-share bookkeeping set; drop nuclear (and hydro) from `_build_rps_row`. Small diff, structurally unambiguous, cheap tests. **Gate:** the REC dual shifts backcast prices wherever RPS binds, so per rule 22 score the change leave-one-year-out within 2023-2025 on the RPS-binding ISOs (CAISO/NYISO/NEISO) before promotion; register the re-gated bundles per rules 15/16. |
| **Uniform WACC** (`nominal_discount_rate=0.08` for every tech) | **DOCUMENT AS LIMITATION** | Tech-differentiated WACC (ATB financial cases: merchant gas > contracted solar) re-levels *every* entry margin simultaneously and interacts with the calibrated queue caps; there is no admissible observable in-repo to validate the re-leveled entry mix against until the capacity hindcast (W0-P4/W2-P5) exists. Deferred with a named future design: `TECH_WACC_PREMIUM: dict[tech, pp]` cited to ATB 2024 financial assumptions, evaluated against the hindcast when it lands. Until then: limitation paragraph in methodology spec §5 + this doc. |
| **VRE flat-mean entry revenue** (`capacity.py:1268` passes scalar `base_cf`) | **FIX NOW (W2-P3), cheap** | `estimate_expected_revenue` already accepts hourly CF arrays (`capacity.py:958-965`) — the shape-blindness is a call-site artifact. Fix: pass the ISO's zonal hourly CF profile (the same `wind_cf`/`solar_cf` arrays that bound `W`/`S` in dispatch) for the build zone, so solar entry sees its own value cannibalization and wind its diurnal/seasonal capture rate. No new parameters. Expected effect: solar entry slows at high penetration (capture rate < mean price), wind relatively favored — CO₂ direction mildly **up** late-horizon vs today, and structurally correct (rule 1: the flat mean was reaching the right build through an unreal mechanism). |

### 6.1 CX-6a resolution — retirement-screen half landed; RPS-row half deferred (U-03)

**Status (L-7, 2026-07-06):** the *retirement-screen* half of CX-6a is **landed**. The
*RPS-constraint-row* half is **deferred** to a dispatch-owning lane, for the reasons below.

**U-03 reconciliation — both cited sites are live, in different modes:**

| Site | Mechanism | Mode it is live in | Disposition |
|---|---|---|---|
| `capacity.py` retirement screen (`apply_economic_retirements`, the `_CLEAN_FUELS` credit at the `rps_for_unit` line) | Credits the RPS shadow price as retention **revenue** to nuclear/hydro | **Forecast capacity-evolution only** (the screens never run in a backcast — no capacity evolution). **Zero keeper blast radius.** | **FIXED here.** Split `_CLEAN_FUELS` → added `_RPS_ELIGIBLE_FUELS = {wind, solar}`; the screen now credits the RPS shadow only to that set. `_CLEAN_FUELS` retained unchanged for `compute_clean_share` (clean-*accounting* basis, legitimately includes nuclear/hydro). Test: `test_capacity.py::test_nuclear_not_credited_rps_shadow_in_retirement_screen`. The **new-entry** screen was already correct (uses `_RENEWABLE_NEW_FUELS = {wind, solar}`), so only the retirement screen carried the defect. |
| `dispatch.py::_build_rps_row` (nuclear columns on the RPS constraint LHS) | Lets nuclear generation **count toward** the RPS target; its dual is the REC price | Only when `rps_enabled and rps_target > 0` → **forecast / RPS-binding ISOs**. **Verified no-op for every registered keeper**: the keeper solve path (`run_calibration.py`) calls `solve_dispatch(..., rps_target=None)` (line 4195) and `run_calibration_full.py` has zero RPS references, so the RPS row is never built in a scored backcast. | **DEFERRED** to a dispatch-owning lane. Removing nuclear from the row is what revives the REC dual (the §6/§7 "6a: REC dual revives → more VRE entry" effect); it changes **forecast** prices for CAISO/NYISO/NEISO, so it must land with the plan-required LOYO re-score of those keepers **within 2023-2025** (rule 22) and re-gate per rules 15/16. Because it is a no-op for current keepers, this deferral leaves every registered result byte-identical. `dispatch.py` is outside L-7's file ownership (owned by the dispatch/per-ISO lanes), which is the correct home for the coupled re-score. |

**Why the split, not a single edit:** the two sites answer two questions — *does nuclear
count toward RPS compliance?* (`_build_rps_row`) and *does nuclear get paid the REC price?*
(the screen credit). They must agree. CX-6a's decision is *no* on both (RPS = renewable;
nuclear support is ZEC via `eac_price_nuclear`). Landing only the screen half is the
conservative interim: nuclear loses a REC credit it should not have had, and the REC dual
stays (harmlessly, in backcast) depressed by nuclear until the row half lands. No forecast
result is currently promoted, so nothing downstream consumes the half-state.

---

## 7. Interactions & combined emissions outlook

| Item | 2030s forecast CO₂ direction | Main interaction |
|---|---|---|
| 1 FOM ↑ | **Down** (more coal/steam exits) | Must co-move with scarcity revenue (§5) or over-retires into backstop CTs |
| 2 Foresight | **Down** (entry stops lagging growth) | Amplified by item 4's high-DC path; measured by the A/B |
| 3 Floor accreditation + CO₂ tie-break | **Down** (floor binds less; retains gas over coal when it binds) | Uses item 2's known-peak; shares the backstop's PRM constant |
| 4 DC block | **Up** at equal-energy (flatter net load → more mid-merit fossil); **up** absolute on high path | Feeds item 2's growth signal; weakens scarcity → interacts with §5 grid |
| 6a nuclear RPS | Down where RPS binds (REC dual revives → more VRE entry) | Backcast-scored (LOYO) before promotion |
| 6c VRE shape-aware revenue | Slightly up late-horizon (less over-built solar) | Counterweight to 6a; both land together in one tornado refresh |

Net expectation: forecast CO₂ trajectory shifts **down** in the 2030s, with the DC block the
one deliberate upward input correction. The final W2-P3 tornado refresh (all items on)
quantifies the decomposition per the rule-21 ablation discipline.

## 8. Test plan (W2-P3 acceptance)

Trivial-first (CLAUDE.md testing pattern): every mechanism test starts 1-gen/1-zone/24 h.

1. **FOM:** defaults match §1.2 table; `parameters.json` entries present and cited (CI
   `validate_parameters.py` green); tornado registry bands re-centered.
2. **Foresight:** EWMA α=1.0 byte-identical to today (hash of `prior_results["price_signal"]`
   vs `econ_prices`); stack re-price on a 3-unit stack reproduces hand-computed hourly
   prices incl. the scarcity tail; `peak_demand_next` equals `_scale_demand(year).sum(0).max()`.
3. **Floor:** accredited requirement math vs hand-computed UCAP/ELCC sum; retention order
   obeys ($/firm-MW, CO₂) keys on a crafted coal-vs-CT tie; floor never *retires* anything
   (only un-retires); `floor_retention_log` rows complete; with pools=0 the new floor is at
   least as conservative as a nameplate floor at equal margin.
4. **DC block:** off-path byte-identical demand; on-path adds exactly
   `dc_mw × LF × share` to every hour of every zone; energy/peak deltas analytic;
   backcast+non-off validator raises; zone shares sum to 1.
5. **CX-6:** RPS row excludes nuclear/hydro (matrix column check); retirement screen credits
   RPS shadow only to wind/solar; VRE entry called with hourly CF (mock-assert), scalar path
   still supported.
6. Existing `test_capacity.py` / `test_runner.py` green throughout; any behavioural test
   asserting the old floor/`retirement_reserve_margin` updated with citation to this doc.

## 9. W2-P3 implementation prompt (complete — hand to the implementing session verbatim)

```
[OPUS] W2-P3 — Implement capacity-economics recalibration (FOM, foresight, floor, DC load)

Read CLAUDE.md, then docs/handoffs/capacity-economics-plan-2026-07.md (THE PLAN — follow it;
where this prompt and the plan disagree, the plan wins), then docs/fable-repo-audit-2026-07.md
§C. Work on a fresh branch off latest origin/main.

SCOPE GUARD (from the plan §0): you are changing ONLY the annual capacity-evolution layer
(src/market_sim/model/capacity.py screens/floor/backstop, runner.py pre-solve signal + demand
assembly, config/scenarios.py + config/constants.py). You must NOT touch, weaken, or remove
the dispatch-layer temperature-dependent reliability floors (data/floor_mechanisms.py,
model/transmission.py CAISO/NEISO temp limbs) — separate hourly mechanism, stays in. All work
is LP-only, one-pass (rule 10), vectorized (rule 2), rule-24 registered (every new tunable in
ScenarioConfig/constants.py and run_config.json).

Stage order (separate commits, each with tests green; plan §8 is the acceptance list):

1. FLOOR (plan §3.2): rebuild the retirement reliability floor in apply_economic_retirements
   on the accredited basis via accredited_firm_capacity_mw; thread wind/solar/storage-firm
   pools from prior_results as optional args (default 0.0); requirement =
   peak_demand_used × (1 + PLANNING_RESERVE_MARGIN_BY_ISO[iso]); DELETE
   retirement_reserve_margin (rule 26 — removed, not zeroed; migrate its tornado entry to the
   PRM table); retention merit = going_forward_cost per firm MW ascending, CO2 rate
   tie-break; emit floor_retention_log through evolve_fleet and persist per-year
   (floor_retentions.json next to the results parquet). Locational exemption of RA-saturated
   zones only if capacity_deliverability_limits tests stay cheap; else document in the plan.
2. FORESIGHT component 1 (plan §2.3.1, unconditional): compute the entering year's known
   peak (from _scale_demand incl. stage-4 DC block when on) before evolve_fleet and use it in
   the floor and apply_reserve_margin_build in place of prior-year peak.
3. FORESIGHT A/B (plan §2.4): implement entry_price_signal_alpha (EWMA, default 1.0 =
   byte-identical) and entry_lookahead_reprice (stack re-price with ORDC tail, default False,
   screens-only). Run the 4-arm ERCOT high-growth 2026-2040 A/B (plus mid-growth replicate),
   legacy bins, sequential years, ≤2 concurrent invocations; write
   docs/handoffs/foresight-ab-ercot-<date>.md + .json with the plan's metrics; promote per
   the plan's decision rule (>5% 2030-2040 cumulative fossil CO2 AND reduced backstop MW →
   flip that arm's default; otherwise leave default-off and record the negative result).
4. DC BLOCK (plan §4.2): datacenter_load_path/off-low-mid-high, datacenter_load_factor
   (0.85, LBNL 2024 / EPRI 2024 citations), datacenter_percentile;
   DATACENTER_ADDITIONS_MW + DATACENTER_ZONE_SHARE in constants.py with per-ISO citations
   (ERCOT LTLF large-flexible-load, PJM 2025 Load Forecast DC component, NYISO Gold Book,
   CAISO IEPR; an ISO/path with no published source ships 0 — never invent). Additive flat
   block after _scale_demand, zonally allocated, vectorized. IN THE SAME CHANGE re-derive
   DEMAND_GROWTH_RATES near-term rates as organic-ex-DC under the plan's 2030
   energy-continuity constraint, documenting the decomposition per ISO in the constants
   comment and parameter-citations. Config validator: backcast mode + non-off DC path raises.
   Electrification shape adder: config/loader interface only if trivially cheap, else skip
   and leave the plan's limitation note standing.
5. CX-6 fixes (plan §6): (a) remove nuclear AND hydro from the RPS constraint row
   (dispatch._build_rps_row) and restrict the screens' RPS-shadow credit to wind/solar
   (split _CLEAN_FUELS); ZEC support stays via eac_price_nuclear. Then re-score the
   RPS-binding ISOs (CAISO/NYISO/NEISO) leave-one-year-out WITHIN 2023-2025 only (rule 22 —
   2022/H1-2026 remain fully quarantined); if promoted, re-solve those keepers' full year
   spans (rule 16) and register the bundles on the dashboard per rule 15 (calibration-report
   skill), then run the calibration-keeper-auditor agent. (b) VRE shape-aware entry revenue:
   pass the build zone's hourly wind/solar CF profiles into estimate_expected_revenue at
   capacity.py's entry call sites. (c) Uniform WACC: add the plan's limitation paragraph to
   model-methodology-spec.md §5 — no code.
6. JOINT FOM+SCARCITY PROTOCOL, then FOM defaults (plan §5, §1.2 — THIS ORDER, rule 1):
   (i) revenue-side audit of the ERCOT 2023-2025 keeper bundles' screen revenue stack vs
   Potomac SOM net-revenue tables (comparison only — never pin, never add a multiplier);
   (ii) any shortfall is fixed at the mechanism (published ORDC params / endogenous co-opt),
   NEVER via FOM haircut or as_revenue_multiplier sweep; (iii) run the 2×3 ERCOT grid + 2-cell
   PJM check; (iv) flip fixed_om_gas_ct 8→21, fixed_om_gas_cc 12→30, fixed_om_coal 40→45 in a
   dedicated commit ONLY if the plan §5.4 acceptance gates pass (near-term retirement pace in
   the observed band, backstop ≈ 0 in years 1-3), citing
   docs/handoffs/fom-scarcity-joint-protocol-<date>.md; update parameters.json citations
   (ATB 2024 / EIA-S&L) and re-center the tornado FOM bands (low = legacy, high = ATB×1.25),
   adding the paired fom_and_scarcity perturbation.
7. WRAP: full-suite pytest green; refresh the ERCOT tornado (all landed items on) and commit
   the report; update the DOF ledger entries per plan §5 identification table; /sync-docs for
   methodology spec §5.x + CLAUDE.md capacity paragraphs; CHANGELOG entry.

Hard rules: no solve or data intake touching 2022 or H1-2026 (rule 22); forecast probes are
NOT dashboard runs, but every backcast bundle produced in stage 5 IS (rules 15/16); no new
env-var or getattr-fallback knobs (rule 24); commit messages imperative present tense; push
per CLAUDE.md "Git & Pushing" (MCP push_files for anything carrying dashboard payloads).
```

---

*Produced 2026-07-05 (W0-P5, Fable). Code anchors verified against `origin/main` f7fa444.*
