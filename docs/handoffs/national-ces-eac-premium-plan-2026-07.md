# National Clean Energy Standard (CES) EAC-Premium Forecast — Plan (2026-07)

**Status:** PLANNING ONLY — no code changed, no LP solved. This document is the single
source for the build; every wave-session prompt in §8 points back here.
**Owner ask (2026-07-17):** model a *national* CES that credits every clean/low-carbon
resource (including CCS retrofits and new build) with an EAC premium, as a federal
alternative to state RPS/CES. Plug in an ensemble of premium levels and compare
plant-level revenue and capacity expansion against a BAU case. Test ISOs: ERCOT + PJM;
the module must work for any ISO, with the premium settable to any level and able to
track inflation over time.

---

## 0. TL;DR

Most of the architecture exists. `policy/eac.py` already implements exogenous per-tech
EAC prices that (a) lower dispatch offers (`apply_eac_to_mc`, `compute_eac_dispatch_credits`)
and (b) raise retirement/new-entry/CCS-retrofit economics via the
`max(eac, rps_shadow)` no-stack rule (`model/capacity.py:240`). The model is real-2026$
throughout (`REAL_DOLLAR_BASE_YEAR`, constants.py:483) — **a flat premium already tracks
inflation in nominal terms**; nominal display is post-processing
(`results/export.py::real_to_nominal`). The deterministic scenario-matrix runner
(`matrix.py`, `SweepDefinition` cases mode) is purpose-built for a premium ladder, and
`check_forecast_invariants.py` is the ready-made QA gate.

What's missing, in order of importance:
1. **No year variation / escalation** on any EAC price (flat scalars; no `year` arg
   anywhere in the EAC path).
2. **No national-CES layer**: no uniform premium across techs, no carbon-intensity
   crediting, and the candidate techs `nuclear_smr` / `hydrogen_ct` / `hydrogen_ccgt`
   earn **zero** attribute revenue (absent from `_EAC_PRICE_FIELDS`), so a CES premium
   today cannot pull new nuclear or hydrogen.
3. **45Q is absent from the CCS *retrofit* screen** (present only in new-build CCS
   LCOE) — BAU under-values retrofits, which would corrupt the CES-vs-BAU retrofit delta.
4. **No PJM forecast config** (ERCOT-only YAMLs); PJM BAU must be assembled and smoked.
5. **No attribute-revenue line in `plant_financials.py`** and no captured-price /
   negative-price-hours / clean-share diagnostics in the committed output surface.
6. **Known-weak capacity screens** (open `forecast-retirement-calibration` lane):
   PJM retires ~nothing, ERCOT over-retires with zero solar entry. Capacity-expansion
   deltas carry this caveat until that lane lands (§7).

Build is organized as 4 sequential waves of parallel session prompts (§8):
W1 foundations (config+resolver / PJM+ERCOT BAU smoke / CI-crediting audit),
W2 integration (consumer wiring / reporting), W3 campaign (ERCOT / PJM ladders +
synthesis), W4 optional (endogenous CES constraint, sampler dimension).

---

## 1. What we are modeling

A federal clean-energy standard in which every credited MWh earns one Energy Attribute
Certificate (EAC) and the model takes the **EAC price as an exogenous scenario input** —
an ensemble of premium levels — rather than clearing the federal certificate market
endogenously. Rationale:

- Each ISO solves its own LP; a *national* certificate market cannot clear inside one
  ISO's dispatch problem. An exogenous price applies uniformly to every ISO (exactly how
  `eac_price_*` already works) and sidesteps cross-ISO clearing.
- The owner's question is a price→response map ("what does premium X do to revenue and
  buildout"). The inverse map (what premium clears a target clean share) is read off the
  resulting clean-share-vs-premium curve, one point per ladder case.
- An endogenous ISO-level CES constraint (a generalized RPS row whose dual is the EAC
  price) remains available as a Wave-4 cross-check — same machinery as
  `_build_rps_row` (dispatch.py:486-538), CI-weighted.

**Crediting.** Two schemes, config-selectable (D1, §4):
- `carbon_intensity` (recommended default): credit fraction per unit
  `f_g = clip(1 − CI_g / benchmark, 0, 1)` with `benchmark = 0.82 t CO2/MWh` — the
  partial-crediting design of the Clean Energy Standard Act (Smith, S.1359, 116th Cong.)
  and Bingaman's CESA 2012 (S.2146). Zero-carbon fuels get 1.0; a 90%-capture CCS unit
  ~0.95; unabated efficient gas CC ~0.55 **only if** `federal_ces_unabated_fossil_eligible`
  (default off). Per-unit CI comes from the fleet's own forward CO2 rates
  (CAMPD/CEMS-derived, all six ISOs, tonnes/MWh at the LP boundary —
  `data/emission_rates.py::forward_plant_co2_rate`).
- `binary`: fraction 1.0 for every fuel in the eligible set, 0 otherwise (RPS-like).

**Interaction with existing policy:**
- **State RPS/EAC:** house doctrine is one certificate per MWh, sold once —
  attribute revenue is `max()`, never a sum (`policy/eac.py:12-16`, `capacity.py:240`).
  The federal premium joins that same `max()` family against the legacy `eac_price_*`
  scalars and the RPS dual. For ERCOT and PJM this is moot in practice: neither has an
  RPS row (`STATE_RPS_FLOORS` ERCOT all-0.0, PJM no entry; constants.py:3873-3895), so
  the premium is the *only* attribute mechanism in both test ISOs.
  `federal_ces_replaces_state_rps` (default off) additionally suppresses state RPS rows
  for a pure-federal counterfactual in RPS ISOs (CAISO/NYISO/NEISO).
- **Tax credits (PTC/ITC/45U/45Q):** separate instruments, and they keep their existing
  conventions — the wind PTC stacks with EACs in dispatch offers (test_eac.py:98), §45U
  stays inside the retirement screen's `max()` seam (ira.py:90-92, no-stack test
  test_capacity.py:3181), 45Q stays a revenue/LCOE term. No convention changes.

**Dollars.** All premiums are **real 2026$/MWh** (model-wide convention,
scenarios.py:45-47). A constant real premium *automatically* rises with inflation in
nominal terms (≈2.2%/yr, `INFLATION_RATE`), which is the owner's "increase with
inflation" default. `federal_ces_premium_escalation_real` adds real growth on top;
nominal display uses `results/export.py::real_to_nominal` (post-processing only).

**Eligibility (default):** nuclear (existing + SMR new-build), wind, solar, hydro,
geothermal, offshore wind, gas-CC-CCS (retrofit + new-build), hydrogen turbines.
Excluded by default: unabated fossil (toggle), storage discharge (no new attribute is
created by discharging stored energy; avoids double-crediting the charged MWh — D5),
biomass (immaterial in ERCOT/PJM; biogenic CI accounting would need its own carve-in).
No vintage restriction — existing units credit like new ones (owner's "every clean
resource"; a vintage gate is a cheap follow-on if wanted).

---

## 2. What already exists (verified inventory)

| Component | Where | State |
|---|---|---|
| Exogenous EAC prices, 7 techs, tier 1 | `scenarios.py:211-219`, `TIER_TAGS:6507-13` | ✅ flat scalars, default 0.0 |
| Dispatch-side EAC (thermal MC + wind/solar adders + storage discharge credit) | `policy/eac.py:43-97`; applied once pre-P0 at `runner.py:1088-1094,1141`, carried through P1 | ✅ year-blind |
| Negative renewable offers / keep-running REC value | `eac.py:100-136`, `negative_renewable_offers` | ✅ |
| Attribute revenue in retirement screen (`max(eac, rps_shadow)`, 45U folded in) | `capacity.py:218-241,1418-1443` | ✅ nuclear + gas_cc_ccs only (screen is thermal-only by design) |
| Attribute revenue in new-entry screens | `capacity.py:2229-2236` (emerging), `2399-2406` (classic) | ✅ wind/solar/gas_cc_ccs/geothermal/osw; ❌ nuclear_smr, hydrogen (no `_EAC_PRICE_FIELDS` key) |
| CCS retrofit screen with EAC term | `capacity.py:2838-2981` (term at `:2928`); wired `runner.py:781`; retrofits become `gas_cc_ccs` (`:2972`) and inherit dispatch/retirement credits | ✅ but ❌ no 45Q term (new-build has it, `:2742`) |
| RPS LP row + ACP escape + dual feed to next-year screens | `dispatch.py:486-538,2779-82,4008-11`; `runner.py:756-777,1183-91,1978` | ✅ (no row for ERCOT/PJM) |
| IRA credits incl. OBBBA phaseouts; `policy_bundle` resolver | `policy/ira.py`; `scenarios.py:6251-6285` | ✅ |
| Real-dollar convention + nominal conversion | `constants.py:483-488`; `export.py:43-62` | ✅ |
| Forecast orchestration (`market-sim run/matrix/ensemble/sweep`) | `runner.py:2159-2288`; year loop `:387` | ✅ defaults ARE the keeper-calibrated BAU |
| Scenario matrix (named cases, ≤2 concurrent, envelope outputs) | `matrix.py`; `configs/scenario_matrix.yaml` | ✅ summary is emissions-only today |
| PB-2 sampler / ensemble bands | `uncertainty.py` (dims frozen), `ensemble.py:65-71,503,661-763` | ✅ metric-agnostic bands; no premium dim |
| Forecast QA gate (I1-I14 + paired P1-P3) | `scripts/check_forecast_invariants.py` | ✅ |
| Committed forecast golden WITH capacity evolution | `tests/golden/ercot_2026_2040.json` (builds ±10%) | ✅ ERCOT 2026-2040 |
| Evolution ledger (per-year builds/retire/retrofit/fuel-MW/rps_dual + gated per-candidate entry economics) | `evolution_ledger.py:17-42`; `runner.py:2079-2115`; `entry_screen_diagnostics` | ✅ the CES-vs-BAU capacity diff surface |
| Plant financials + 2-scenario delta CSVs | `plant_financials.py` via `scripts/generate_financial_reports.py`; `scripts/compare_scenarios.py:151-173` | ✅ energy+capacity revenue; ❌ no attribute line |
| Forward per-plant CO2 rates, all 6 ISOs | `data/emission_rates.py:155-228` (t/MWh at boundary `:250-253`; class-median fallback) | ✅ CI-crediting input |
| Reference EAC price ranges (documentation) | `constants.py:4786-4801` | ✅ $2–40/MWh by tech |
| Prior art: annual EAC price series (sparse knots, forward-fill), breakeven derivation | `scope2-lce-portfolio/` (standalone, NOT importable): `data/eac/eac_prices.csv`, ADR 0020/0021 | ✅ pattern only |

No prior national/federal CES work exists anywhere in the repo (docs grep clean) — the
feature is genuinely new; its precedents are `STATE_RPS_FLOORS` (year-knot trajectory,
linear interpolation, `rps.py:8-39`) and the `eac_price_*` scalars.

## 3. Gaps

- **G1 — Year variation.** All EAC consumers are year-blind (`apply_eac_to_mc(mc, fleet,
  config)`, `compute_eac_dispatch_credits(config)`, `get_eac_price_for_new_entry(tech,
  config)`). A premium path (escalation or knots) is net-new machinery.
- **G2 — National layer.** No uniform premium, no credit-fraction concept, no CI-based
  crediting, `nuclear_smr`/`hydrogen_*` unmapped (zero attribute revenue), hydro/biomass
  have no EAC field at all (hydro is dispatch-inert to a premium — monthly-budget
  constrained — but matters for revenue reporting).
- **G3 — 45Q retrofit parity.** Retrofit screen's only clean-revenue term is
  `eac_price_ccs` (`capacity.py:2928`); statutory 45Q (~$85/t × ~0.33 tCO2/MWh captured
  ≈ high-$20s/MWh through `ira_ccus_45q_last_year`) is missing, while new-build CCS gets
  it (`:2742`). With every `eac_price_*` = 0, **BAU produces zero retrofits for the wrong
  reason**, inflating the premium's apparent retrofit effect. Fix in W2-A (D6).
- **G4 — PJM forecast BAU.** No committed PJM forecast YAML or validated PJM forecast
  run; ERCOT has base YAMLs + a 2026-2040 golden.
- **G5 — Reporting.** No attribute-revenue line item; no captured-price-by-tech,
  negative-price-hours, clean-share, premium-capture metrics in committed outputs
  (raw material — per-gen dispatch × zonal prices — is persisted).
- **G6 — Campaign harness.** No premium-ladder matrix YAML, no CES-vs-BAU report script
  (capacity deltas from ledgers + revenue deltas from financials + saturation curves).
- **G7 — Spec/doc gap.** `model-methodology-spec.md` documents neither the `eac_price_*`
  mechanism nor the `max(eac, rps_shadow)` rule (code-only today).
- **G8 — Registration hygiene.** New fields must follow the full checklist: dataclass
  default + source comment → `TIER_TAGS` → `parameters.json` citation
  (`validate_parameters.py` fails CI otherwise) → `_CACHE_KEY_OPTIONAL_FIELDS`
  (cache-key neutrality at default) → `__post_init__` backcast guard (rule 13, mirror
  `gas_price_factor:5789-94`) → ONE delivery channel (never both an explicit kwarg and
  `prb_overrides`; recorder must mirror live order — the ERCOT-65 lesson).

## 4. Design decisions

Settled (recommendation baked into §5 spec; each is a config field, so reversal is cheap):

- **D1 Crediting default = `carbon_intensity`**, benchmark 0.82 t/MWh (CESA-cited),
  `binary` available. Unabated fossil ineligible by default (toggle) — OPEN-1.
- **D2 Attribute stacking = `max()`** across federal premium / legacy `eac_price_*` /
  RPS dual (house doctrine); tax credits keep their existing separate conventions.
- **D3 Premium path = real 2026$**, `base × (1+escalation_real)^(y−2026)`, or explicit
  `{year: value}` knots with linear interpolation (RPS-floor pattern), edge-held.
  Flat real = CPI-tracking nominal (owner's default ask) — OPEN-4 confirms.
- **D4 Exogenous price ladder now** (matrix cases); endogenous constraint is W4.
- **D5 Storage discharge not credited** by default (no new attribute; avoids
  double-credit) — toggle exists; ELCC/arbitrage effects still flow to storage via
  prices. — OPEN-5.
- **D6 45Q retrofit-parity fix ships in W2-A** (rule 14: statutory revenue term missing
  is a discovered bug; required for an honest CES-vs-BAU retrofit delta). Enters as its
  own term mirroring new-build treatment (expiry via `ira_ccus_45q_last_year`), with the
  `eac_price_gas_cc_ccs` docstring updated to drop its "45Q proxy" role. — OPEN-6.
- **D7 Premium applies to BOTH dispatch offers and capacity economics** (existing EAC
  architecture; the offer side is what makes saturation/cannibalization real, §6).
- **D8 Campaign = 2026-2040, ladder {5,10,15,20,30} + BAU 0**, both ISOs — OPEN-3.

Open for owner (defaults proceed if unanswered; none block W1):

- **OPEN-1** Unabated efficient gas partial credit (full CESA design): default OFF —
  flip `federal_ces_unabated_fossil_eligible` per case to test.
- **OPEN-2** Existing-resource eligibility: default = existing units credit fully
  (hydro/nuclear included). Alternative (CEPP-style new/incremental-only) = follow-on
  vintage gate.
- **OPEN-3** Horizon & ladder: 2026-2040 recommended (golden-validated horizon, ~halves
  runtime vs 2050); ladder {5,10,15,20,30} real $/MWh (spans REC/ZEC/OREC reference
  ranges, constants.py:4786-4801, and the scope2 CCS breakeven ≈$20).
- **OPEN-4** Escalation default 0%/yr real (nominal-flat instead would be −2.2%/yr real).
- **OPEN-5** Storage discharge crediting (default no).
- **OPEN-6** Confirm 45Q retrofit-parity fix in scope (recommended yes).
- **OPEN-7** Accept capacity-screen caveat (§7) and proceed now (recommended), or block
  W3 on the forecast-retirement-calibration lane.

## 5. Specification

### 5.1 Config surface (all Tier 1, default-off ⇒ byte-identical when disabled)

```python
# --- National CES (federal EAC premium) ---------------------------------
federal_ces_enabled: bool = False
federal_ces_premium_usd_per_mwh: float = 0.0     # real 2026$/MWh at 2026
federal_ces_premium_escalation_real: float = 0.0 # real annual growth; 0 = CPI-tracking nominal
federal_ces_premium_by_year: dict[int, float] | None = None  # sparse knots, linear interp,
                                                 # edge-held; overrides base+escalation.
                                                 # YAML round-trip: coerce str keys → int.
federal_ces_crediting: str = "carbon_intensity"  # "carbon_intensity" | "binary"
federal_ces_ci_benchmark_t_per_mwh: float = 0.82 # CESA S.1359 (116th) / S.2146 (112th)
federal_ces_eligible_fuels: list[str] = [nuclear, wind, solar, hydro, geothermal,
                                         offshore_wind, gas_cc_ccs, hydrogen_ct, hydrogen_ccgt]
federal_ces_unabated_fossil_eligible: bool = False
federal_ces_storage_eligible: bool = False
federal_ces_replaces_state_rps: bool = False
```

Registration per G8 checklist. `__post_init__`: raise if `federal_ces_enabled` in
backcast mode (forecast-only lever, rule 13). Candidate-tech name mapping (new entry):
`nuclear_smr→nuclear-class 1.0`, `hydrogen_ct/ccgt→1.0`, `gas_cc_ccs→1−(class CI×(1−ccs_capture_rate))/benchmark`,
`wind/solar/geothermal/offshore_wind→1.0`, others 0.

### 5.2 New module `src/market_sim/policy/federal_ces.py`

```python
premium_for_year(config, year) -> float          # 0 unless enabled; knots or base×(1+esc)^n
unit_credit_fractions(config, fleet) -> np.ndarray   # (n_gen,), vectorized (rule 2);
    # binary: eligible-fuel mask; CI: mask × clip(1 − emission_rate/benchmark, 0, 1);
    # + unabated-fossil branch. fleet.emission_rate is t/MWh at the LP boundary.
tech_credit_fraction(config, tech) -> float      # candidate-tech table above
effective_eac_price_for_tech(config, tech, year) -> float
    # max(get_eac_price_for_new_entry(tech, config), premium_for_year × tech_credit_fraction)
effective_unit_eac_prices(config, fleet, year) -> np.ndarray
    # max(legacy per-fuel scalar broadcast, premium × unit_credit_fractions)
```

Unit tests first at trivial scale (1 gen / 24 h — repo testing pattern), including:
disabled ⇒ all-zeros & legacy pass-through; escalation vs knots; CI clipping; CCS
residual-CI fraction; str-key coercion; backcast guard.

### 5.3 Consumer wiring (W2-A; exact seams)

| Seam | Site | Change |
|---|---|---|
| Thermal dispatch MC | `runner.py:1094` → `eac.py:43` | `apply_eac_to_mc(mc, fleet, config, year)`: subtract `effective_unit_eac_prices` (covers nuclear/ccs/geo/osw + hydro/hydrogen; hydro ≈ dispatch-inert, harmless) |
| Wind/solar/storage credits | `runner.py:1141` → `eac.py:83` | `compute_eac_dispatch_credits(config, year)`: `max(legacy, premium×1.0)`; storage only if `federal_ces_storage_eligible` |
| Retirement screen | `capacity.py:1418` | effective price via `effective_eac_price_for_tech(..., year)`; 45U `max()` fold unchanged |
| New entry (emerging + classic) | `capacity.py:2229-36, 2399-2406` | replace inlined `max()` with resolver → **nuclear_smr & hydrogen now earn the premium** |
| CCS retrofit screen | `runner.py:781` → `capacity.py:2928` | attribute term = `max(eac_price_gas_cc_ccs, premium×retrofit_fraction)`; **plus new 45Q term** (D6) mirroring `:2742`, expiring per `ira_ccus_45q_last_year` |
| State-RPS suppression | `runner.py:1183-91` | if enabled & `replaces_state_rps`: skip RPS row (rps_target → None) |

Invariants: screens keep consuming EAC-free `mc_cost` (cost/revenue separation,
`runner.py:1977`); dispatch application stays once-pre-P0; no new LP rows.
**Neutrality proof:** with `federal_ces_enabled=False`, dispatch bytes and
`cache_key` are identical to main (golden + `_CACHE_KEY_OPTIONAL_FIELDS`).

### 5.4 Reporting (W2-B)

- `plant_financials.py`: add `attribute_revenue` (= effective unit premium × generation)
  and `attribute_price_usd_per_mwh` columns; plumb config/year through
  `generate_financial_reports.py`. (PTC/45Q stay out of this line — tax credits, not
  certificates; noted in column docs.)
- `export.py::_summarize_year` + `ensemble._SCALAR_METRICS` (additive): `clean_share`
  (= Σ credit-weighted generation / total generation), `negative_price_hours`.
- New `scripts/report_ces_campaign.py`: reads a matrix out-dir (`meta.json` cases →
  cache keys) + evolution ledgers + financial parquets; emits per-ISO CSV/MD:
  capacity-by-fuel deltas vs BAU per year, builds/retirements/retrofit deltas (ledger),
  plant/company revenue deltas (reusing `compare_scenarios.py` conventions),
  captured price by tech, curtailment by tech, premium-capture rate
  (credited-delivered/potential MWh), clean-share-vs-premium curve, optional nominal-$
  columns via `real_to_nominal`.

## 6. How premiums interact with saturation & cannibalization

The owner's open question — answered structurally, not by assumption:

1. **Offer-side**: credited resources bid down to −(tax credits + premium×fraction)
   (wind: −PTC−premium; nuclear/CCS: mc−premium). In surplus hours the marginal credited
   MWh sets prices as low as its negative keep-running value, so the premium *deepens*
   negative/zero-price epochs as penetration grows — the real CES/PTC dynamic. The
   existing dump-cost guard already prevents credit-farming of curtailed energy
   (objective: `dump_cost = max(ε, −min(wind_mc, solar_mc)+ε)`).
2. **Delivered-only payment**: premium revenue accrues to *dispatched* MWh. Curtailment
   erodes premium capture automatically; the premium-capture-rate metric reports it.
3. **Price cannibalization**: captured energy price by tech = dispatch-weighted LP duals,
   which fall in clean-heavy hours as buildout proceeds. Total unit revenue = captured
   price + premium + (capacity/AS where applicable) — reported per plant.
4. **Capacity-evolution feedback**: entry proceeds while premium-inclusive margin clears
   the screen; each ladder case runs the full one-pass evolution 2026→2040, so
   saturation, storage response, retirements and CCS retrofits equilibrate per premium
   level. The ladder therefore traces the **clean-share-vs-premium response surface**
   (and its inverse: the premium needed for a target clean share), with
   `entry_screen_diagnostics` recording exactly how much the premium moved each
   candidate's margin each year.

## 7. Trust boundaries (read before quoting campaign results)

The forecast retirement/entry screens are the model's documented weak frontier
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md`, lane mostly OPEN):
capacity-market ISOs economically retire ≈ nothing (payment clears 1.26–4.92× FOM —
PJM), ERCOT over-retires ~15× with zero in-year scarcity formation, and **solar new
entry is zero in both ISOs against 25.1 / 13.1 GW actuals (BLK-8)**. Consequences:

- Emissions, price, dispatch, and *plant-revenue* deltas are the trustworthy outputs.
- Absolute capacity-expansion paths are not; CES-vs-BAU *capacity deltas* are
  directionally informative but inherit BAU biases (e.g. premium-induced solar entry may
  overstate the true delta because BAU should already build solar).
- W3 reports MUST carry this caveat block verbatim, and W3-C re-checks the lane's status
  (RC/BLK items) at run time — if BLK-8/RC-1A have landed by then, re-run the ladder on
  the improved screens before drawing capacity conclusions (OPEN-7).

## 8. Build plan — waves of parallel session prompts

Waves run **sequentially**; prompts within a wave are **independent parallel sessions**
(disjoint files). Every session: start from latest `origin/main`; push via
`mcp__github__push_files` only (never `git push`; verify any pushed file ≥300 lines);
NO new GitHub Actions workflows; NO solves on CI runners. Core-infrastructure sessions
(`src/market_sim/`, `scripts/run_*/score_*`, spec, workflows) are **Opus/Fable only**
(rule 27); W1-C is the only Sonnet-eligible prompt. Each prompt is self-contained and
cites this plan (§ references).

### Wave 1 (parallel: W1-A, W1-B, W1-C)

**W1-A — Core config surface + `policy/federal_ces.py` resolver (Opus/Fable)**
Implements §5.1 + §5.2 ONLY (no consumer wiring — solver-inert by construction).
Acceptance: full G8 registration checklist; unit tests incl. neutrality
(`federal_ces_enabled=False` ⇒ zeros/legacy pass-through, cache_key unchanged at
defaults via `_CACHE_KEY_OPTIONAL_FIELDS`); backcast guard raises; `pytest tests/`
green; `python scripts/validate_parameters.py` green.

**W1-B — ERCOT + PJM forecast-BAU readiness smoke (Opus/Fable)**
Creates `configs/scenarios/{ercot,pjm}_ces_base_2026_2040.yaml` (mode: forecast,
`entry_screen_diagnostics: true`) + 2026-only smoke variants; runs both 1-year BAU
smokes in-session; runs `check_forecast_invariants.py`; documents PJM blockers (there is
no committed PJM forecast config today — expect issues) in
`docs/handoffs/ces-w1b-bau-smoke-2026-07.md`. Fix-forward only trivial config-level
issues; report (don't fix) anything structural.

**W1-C — CI-crediting input audit (Sonnet-eligible; additive docs only)**
Audits per-plant forward CO2-rate coverage for ERCOT+PJM forecast fleets
(measured vs `class_fallback` shares from `emission_rates.py` provenance; unit check
t/MWh at boundary), computes the implied credit-fraction distribution by fuel at
benchmark 0.82 (both crediting modes), drafts the CESA/Bingaman citation packet +
`parameters.json` entries for W1-A's constants, and sanity-checks the ladder against
`EAC_PRICE_REFERENCE` + scope2 breakevens. Deliverable:
`docs/handoffs/ces-ci-crediting-audit-2026-07.md`.

### Wave 2 (parallel: W2-A, W2-B; requires W1-A merged, reads W1-B/C reports)

**W2-A — Consumer wiring + 45Q retrofit parity (Opus/Fable)**
Implements §5.3 exactly (six seams table), incl. the `nuclear_smr`/`hydrogen` candidate
mapping and the D6 45Q retrofit term (unless OPEN-6 vetoed). Neutrality golden:
CES-off run byte-identical vs main (existing goldens pass untouched). Integration tests:
premium moves entry margins/retrofit payback/retirement retention in trivial fixtures;
year-escalation visible across two solved years. Updates `model-methodology-spec.md`
(§1.4 + §5.x: EAC mechanism, max() rule, federal CES layer — closes G7).

**W2-B — Reporting & comparison harness (Opus/Fable)**
Implements §5.4: `plant_financials.py` attribute line, `_summarize_year` +
`_SCALAR_METRICS` additive metrics, `scripts/report_ces_campaign.py`,
`configs/ces_premium_matrix.yaml` (cases: `BAU: {}` + `CES-05/10/15/20/30`
setting `federal_ces_enabled` + premium). Tests on synthetic cached fixtures.

### Wave 3 (W3-A ∥ W3-B with workers=1 each — rule 12: ≤2 solves in flight total —
or sequentially with workers=2; then W3-C)

**W3-A / W3-B — ERCOT / PJM premium-ladder campaigns**
`market-sim matrix --config configs/scenarios/<iso>_ces_base_2026_2040.yaml
--matrix configs/ces_premium_matrix.yaml --workers <1|2>` run in-session (background
bash, per-year caching makes interrupts resumable; years always sequential). Gate every
case with `check_forecast_invariants.py` (+ paired CES-vs-BAU direction check);
`generate_financial_reports.py` per case; `report_ces_campaign.py`; commit the matrix
bundle + report doc (§7 caveat block mandatory). Budget: ~2.7 h/leg × 6 legs/ISO
(recorded ERCOT 2026-2040 timing); GB-scale RAM per solve.

**W3-C — Synthesis + docs**
Cross-ISO synthesis memo (clean-share-vs-premium curves, revenue decomposition by
plant/company, retrofit/new-build attribution, cannibalization metrics), re-check of the
retirement-lane status (§7/OPEN-7), owner decision review, `/sync-docs`.

### Wave 4 (optional, owner call)
Endogenous ISO-level CES constraint (CI-weighted `_build_rps_row` generalization + ACP
analog) as a cross-check of the exogenous ladder; premium as a PB-2 sampler dimension or
`policy_bundle` extension (`resolve_policy_bundle` doesn't touch `eac_price_*` today).

## 9. Rule-compliance checklist

- Rule 22 quarantine: forecast-mode 2026+ only; no measured H1-2026 actuals anywhere —
  unrestricted. Backcast guard makes the lever un-usable as a backcast tuning channel
  (rule 13).
- Rule 24 (no off-registry knobs): every parameter is a ScenarioConfig field in
  `TIER_TAGS` + `parameters.json`; one delivery channel (ERCOT-65 lesson).
- Rule 5 / citations: benchmark + defaults cited (CESA S.1359, S.2146, NY ZEC,
  PJM GATS ranges already in `EAC_PRICE_REFERENCE`).
- Rules 2/6: credit fractions vectorized over the fleet arrays; no hour loops.
- Rule 27: core sessions Opus/Fable; push_files with ≥300-line verification.
- Rules 15/16 (backcast dashboard) do not govern forecast campaigns; W3 deliverables are
  committed matrix bundles + reports under `results/ensemble/` + `docs/handoffs/`.
- CLAUDE.md CI policy: all solves in-session; no per-task workflows.

## 10. Owner decision register

OPEN-1..OPEN-7 in §4. Defaults proceed if unanswered; flips are config-level except
OPEN-6 (scope) and OPEN-7 (sequencing).
