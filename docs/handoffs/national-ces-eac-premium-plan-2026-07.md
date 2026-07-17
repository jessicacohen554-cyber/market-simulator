# National Clean Energy Standard (CES) EAC-Premium Forecast — Plan (2026-07)

**Status:** PLANNING ONLY — no model code changed, no LP solved. This document is the
single source for the build; every wave-session prompt in §8 points back here.
**v2 (2026-07-17):** owner resolved the decision register (§4/§10) — crediting redesigned
to two owner-specified modes, horizon 2050 with ladder {10,20,30}, CCS-retrofit treatment
pulled into a dedicated design discussion (§11), and the campaign wave **gated on fixing
the capacity screens first** (§7, "build the code & architecture to do it right").
**v2.1 (2026-07-17):** first campaign scoped to `clean_capture` crediting only —
`cesa_ci` (efficient-CCGT) ships as a built, tested option but does not run in the
initial campaign (owner).
**v2.2 (2026-07-17):** §11 Q1–Q4 resolved by owner — 45Q stacks with the premium;
12-year 45Q credit window modeled with an indefinite-extension option; the fixed 55%
screen CF is REMOVED in favor of economics-based utilization (attainable margin at
post-retrofit costs); assumed capture fraction default 0.95 (target rate; 0.90
sensitivity). Q5 (interim retrofit behavior) still open.
**v2.3 (2026-07-17):** Q5 closed (interim = leave legacy behavior; campaign is gated
anyway). Owner's retrofit-or-retire framing added as a hard W2-C requirement: the
**joint three-way choice** (stay unabated / retrofit / retire) for retrofit-eligible
gas-CCs — today's step order retires units (step 2) before the retrofit screen (step 4)
ever sees them, and the screen must value the retrofit as the INCREMENTAL uplift over
the unit's best unabated continuation. §11 discussion fully resolved; W2-C is
design-complete and blocked only on W1-A merging.
**v2.4 (2026-07-17):** WAVE 1 COMPLETE and merged to main — W1-A (config surface +
`policy/federal_ces.py`, PR #2378), W1-B (BAU smokes: ERCOT 14/14 PASS; PJM 12/14 with
the I7 adequacy-accounting FAIL diagnosed as B1, PR #2379 + report
`ces-w1b-bau-smoke-2026-07.md`), W1-C (crediting audit
`ces-ci-crediting-audit-2026-07.md`, PR #2375). New gaps from W1-B: **G10** (PJM
adequacy side-registries omit DR/firm ties — blocks §7 R4 for PJM), **G11** (F923
measured H1-2026 fuel costs leak into forecast mode — rule-22 hygiene), **G12**
(confirmed-exits clean-partition/`sys.path` silent-degradation hardening). One W1-A
deviation: `federal_ces_ccs_capture_fraction` merged at 0.90 (session launched before
the owner's Q4 → 0.95 call) — flip queued as W2-A task 0. Wave 2 adds **W2-D** (PJM
adequacy intake) and **W2-E** (F923 forecast mode-gate, owner-approved approach).
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
2. **No national-CES layer**: no uniform premium, no credit-fraction concept, and the
   candidate techs `nuclear_smr` / `hydrogen_ct` / `hydrogen_ccgt` earn **zero** attribute
   revenue (absent from `_EAC_PRICE_FIELDS`), so a CES premium today cannot pull new
   nuclear or hydrogen.
3. **CCS-retrofit economics need their own redesign** (§11 — discussion now RESOLVED,
   v2.2/v2.3): no 45Q term (new-build has it), a fixed 0.55 screen CF, an undiscounted
   payback criterion, and no joint retrofit-vs-retire choice (retirement step 2 runs
   before the retrofit screen step 4). W2-C implements the full resolution.
4. **No PJM forecast config** (ERCOT-only YAMLs); PJM BAU must be assembled and smoked.
5. **No attribute-revenue line in `plant_financials.py`** and no captured-price /
   negative-price-hours / clean-share diagnostics in the committed output surface.
6. **Known-weak capacity screens** (open `forecast-retirement-calibration` lane):
   PJM retires ~nothing, ERCOT over-retires with zero solar entry. **Owner decision
   (OPEN-7): these are fixed BEFORE any meaningful campaign run** — the campaign wave is
   gated on the screen-readiness criteria in §7.

Build waves (§8): W1 foundations (config+resolver / BAU smoke / crediting audit) →
W2 integration (consumer wiring minus retrofit seam / reporting / CCS-retrofit design
resolution) → W3 capacity-screen readiness gate (external lane + verification) →
W4 campaign (2026-2050, BAU + {10,20,30}, `clean_capture` mode; the `cesa_ci` ladder is
parked as a turnkey option) → W5 optional (endogenous CES constraint, sampler dimension).

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
  price) remains available as a Wave-5 cross-check — same machinery as
  `_build_rps_row` (dispatch.py:486-538), CI-weighted.

**Crediting (owner decision 2026-07-17 — two modes, both shipped):**
- **`clean_capture` (DEFAULT).** Zero-carbon eligible fuels credit at **1.0**; abated gas
  (gas_cc_ccs, retrofit or new-build) credits at the **assumed capture fraction**
  `federal_ces_ccs_capture_fraction` (default **0.95** — owner 2026-07-17: the target
  capture rate; 0.90 the sensitivity); unabated fossil credits **0**. Simple,
  certificate-like, no per-unit CI dependence.
- **`cesa_ci` (VARIANT).** CESA-style fractional crediting
  `f = clip(1 − CI/0.82, 0, 1)` (benchmark `federal_ces_ci_benchmark_t_per_mwh = 0.82`
  t CO2/MWh — CESA S.1359 116th Cong.; Bingaman S.2146 112th), **extended to unabated
  gas CC whose CI ≤ `federal_ces_unabated_ci_threshold_t_per_mwh = 0.45`** (450 kg/MWh —
  owner-set eligibility line; ≈ the EPA §111(b) new-CCGT NSPS of 1,000 lb CO2/MWh, W1-C
  finalizes the citation). An efficient CCGT at ~0.37 t/MWh earns ~0.55; units above the
  0.45 line earn 0 regardless of the benchmark formula. Abated gas earns the same CESA
  formula on its residual CI (≈0.955 at 90% capture). Per-unit CI comes from the fleet's
  own forward CO2 rates (CAMPD/CEMS-derived, all six ISOs, tonnes/MWh at the LP
  boundary — `data/emission_rates.py::forward_plant_co2_rate`).
  *Interpretation note (flagged for owner):* 0.45 is read as an **eligibility cutoff**
  with the credit fraction still computed against the 0.82 benchmark — not as the
  denominator. Correct in review if the intent was `1 − CI/0.45`.
  *Scope (owner 2026-07-17):* `cesa_ci` ships as a selectable option; the **first
  campaign runs `clean_capture` only**.

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
  test_capacity.py:3181). 45Q treatment for retrofits is part of the §11 discussion.

**Dollars.** All premiums are **real 2026$/MWh** (model-wide convention,
scenarios.py:45-47). A constant real premium *automatically* rises with inflation in
nominal terms (≈2.2%/yr, `INFLATION_RATE`) — the owner's confirmed default
(escalation_real = 0). `federal_ces_premium_escalation_real` remains available for real
growth; nominal display uses `results/export.py::real_to_nominal` (post-processing only).

**Eligibility (default; owner-confirmed):** nuclear (existing + SMR new-build), wind,
solar, hydro, geothermal, offshore wind, gas-CC-CCS (retrofit + new-build), hydrogen
turbines. **Existing clean units credit identically to new ones** (owner decision — no
vintage gate). Excluded: unabated fossil in `clean_capture` mode (the `cesa_ci` variant
is the unabated-CCGT pathway), storage discharge (owner-confirmed — discharging stored
energy creates no new attribute; storage adapts endogenously to VRE via arbitrage),
biomass (immaterial in ERCOT/PJM; biogenic CI accounting would need its own carve-in).

---

## 2. What already exists (verified inventory)

| Component | Where | State |
|---|---|---|
| Exogenous EAC prices, 7 techs, tier 1 | `scenarios.py:211-219`, `TIER_TAGS:6507-13` | ✅ flat scalars, default 0.0 |
| Dispatch-side EAC (thermal MC + wind/solar adders + storage discharge credit) | `policy/eac.py:43-97`; applied once pre-P0 at `runner.py:1088-1094,1141`, carried through P1 | ✅ year-blind |
| Negative renewable offers / keep-running REC value | `eac.py:100-136`, `negative_renewable_offers` | ✅ |
| Attribute revenue in retirement screen (`max(eac, rps_shadow)`, 45U folded in) | `capacity.py:218-241,1418-1443` | ✅ nuclear + gas_cc_ccs only (screen is thermal-only by design) |
| Attribute revenue in new-entry screens | `capacity.py:2229-2236` (emerging), `2399-2406` (classic) | ✅ wind/solar/gas_cc_ccs/geothermal/osw; ❌ nuclear_smr, hydrogen (no `_EAC_PRICE_FIELDS` key) |
| CCS retrofit screen with EAC term | `capacity.py:2838-2981` (term at `:2928`); wired `runner.py:781`; retrofits become `gas_cc_ccs` (`:2972`) and inherit dispatch/retirement credits | ✅ but ❌ no 45Q term (new-build has it, `:2742`) — see §11 |
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
- **G2 — National layer.** No uniform premium, no credit-fraction concept, no
  mode-based crediting, `nuclear_smr`/`hydrogen_*` unmapped (zero attribute revenue),
  hydro/biomass have no EAC field at all (hydro is dispatch-inert to a premium —
  monthly-budget constrained — but matters for revenue reporting).
- **G3 — CCS retrofit economics.** Multiple defects/simplifications (no 45Q vs
  new-build's `:2742`; fixed `_RETROFIT_SCREEN_CF = 0.55`; undiscounted
  payback-vs-remaining-life; capture-rate field duplication; no joint
  retrofit-vs-retire choice). Resolved in **§11**; implementation lands as W2-C.
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
- **G9 — Capacity-screen fitness.** The retirement/entry screens are not yet fit for a
  meaningful capacity-expansion comparison (§7). Owner: fix before running.
- **G10 — PJM adequacy side-registries (W1-B B1).** `ADEQUACY_DEMAND_RESPONSE_FRACTION_
  BY_ISO` and `ADEQUACY_EXTERNAL_TIE_FIRM_MW` are ERCOT-only, so PJM's accredited firm
  capacity (143,332 MW) sits 5,439 MW below its requirement (148,771 MW) in 2026 and
  **every PJM forecast fails I7** until cited PJM BRA parameters (DR/load-management
  UCAP, CIL firm-import treatment) are intaken. Blocks §7 R4 for PJM. → W2-D. Published
  parameters only — never a number tuned to clear I7 (rules 5/13).
- **G11 — F923 H1-2026 leak into forecast mode (W1-B B2).** `apply_plant_monthly_fuel_
  prices` gates only on year availability (fuel.py:3973-77); with measured 2026 rows now
  intaken, forecast-mode smokes priced ERCOT 12 / PJM 51 generators from measured
  H1-2026 delivered costs — contradicting the overlays-are-backcast-only convention
  (rule 22, spec §1.7) and contaminating the crossover window's forecast side. → W2-E
  (owner-approved approach; also perturbs any 2026+ forecast bytes incl. a golden
  regen — flag in the fix PR). APPROVED: mode-gate (Option 1), owner 2026-07-17.
- **G12 — Silent-degradation hardening (W1-B B3/B4).** `load_confirmed_exits` degrades
  to a warn-only no-op when `data/clean/` is missing or the repo root is off `sys.path`
  (ERCOT 2026 fleet silently gains 477 MW — V H Braunig backlog). Operational rule for
  every runner session: `PYTHONPATH=. python scripts/curate_confirmed_retirements.py`
  before forecasting on a fresh checkout, and caches predating a data fix must be
  deleted (cache_key hashes config only). Code hardening (fail loudly when
  `confirmed_exits_enabled` + forecast + registry unreadable) folds into W2-E.

## 4. Design decisions — RESOLVED (owner, 2026-07-17)

- **D1 Crediting = two owner-specified modes** (§1): `clean_capture` default (clean 1.0,
  CCS = assumed capture fraction 0.95 [0.90 sensitivity], unabated 0) and `cesa_ci` variant (CESA
  formula vs 0.82, unabated CCGT eligible under the 0.45 t/MWh line). Both modes ship in
  W1-A; the **first campaign runs `clean_capture` only** — `cesa_ci` is a built, tested
  option for later runs (owner 2026-07-17). The v1 `binary` mode and
  `federal_ces_unabated_fossil_eligible` boolean are dropped — subsumed by the mode
  choice. *(One interpretation flag on 0.45 — see §1 crediting note.)*
- **D2 Attribute stacking = `max()`** across federal premium / legacy `eac_price_*` /
  RPS dual (house doctrine); tax credits keep their existing separate conventions.
  45Q-vs-premium stacking **for retrofits** is a §11 question.
- **D3 Premium path = real 2026$**, `base × (1+escalation_real)^(y−2026)`, or explicit
  `{year: value}` knots with linear interpolation (RPS-floor pattern), edge-held.
  **Escalation default 0%/yr real confirmed** (= CPI-tracking nominal).
- **D4 Exogenous price ladder now** (matrix cases); endogenous constraint is W5.
- **D5 Storage discharge not credited — confirmed** (storage adapts to VRE via
  arbitrage endogenously; toggle retained for sensitivity).
- **D6 → §11.** The v1 "45Q retrofit-parity fix ships in W2-A" call is superseded: the
  whole retrofit treatment gets a design pass first (owner: "deeper discussion on how to
  handle CCS retrofit in general"). W2-A wires every seam EXCEPT the retrofit screen.
- **D7 Premium applies to BOTH dispatch offers and capacity economics** (existing EAC
  architecture; the offer side is what makes saturation/cannibalization real, §6).
- **D8 Campaign horizon = 2026–2050; first-run ladder = {10, 20, 30}** real $/MWh + BAU,
  **`clean_capture` mode only** (the `cesa_ci` ladder is parked as a ready-to-run
  option), both ISOs (§8 W4).
- **D9 (was OPEN-7) Screens first.** The campaign is **blocked** until the §7 readiness
  criteria are met. "Focus here is building the code & architecture to do it right."

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
federal_ces_crediting: str = "clean_capture"     # "clean_capture" | "cesa_ci" (§1)
federal_ces_ccs_capture_fraction: float = 0.95   # policy-assumed capture crediting for
                                                 # abated gas in clean_capture mode
                                                 # (owner 2026-07-17: 0.95 = target
                                                 # capture rate; 0.90 sensitivity).
                                                 # Distinct from the engineering
                                                 # ccs_capture_rate / ccs_retrofit_capture_rate
                                                 # fields; W1-C reconciles/documents.
                                                 # NOTE: W1-A merged at 0.90 (pre-Q4);
                                                 # the 0.95 flip is W2-A task 0.
federal_ces_ci_benchmark_t_per_mwh: float = 0.82 # cesa_ci benchmark; CESA S.1359/S.2146
federal_ces_unabated_ci_threshold_t_per_mwh: float = 0.45  # cesa_ci-only unabated-CCGT
                                                 # eligibility line (owner-set, 450 kg/MWh;
                                                 # ≈ EPA §111(b) 1,000 lb/MWh — W1-C cites)
federal_ces_eligible_fuels: list[str] = [nuclear, wind, solar, hydro, geothermal,
                                         offshore_wind, gas_cc_ccs, hydrogen_ct, hydrogen_ccgt]
federal_ces_storage_eligible: bool = False       # owner-confirmed default
federal_ces_replaces_state_rps: bool = False
```

Registration per G8 checklist. `__post_init__`: raise if `federal_ces_enabled` in
backcast mode (forecast-only lever, rule 13); validate `federal_ces_crediting` against
the two mode names. Candidate-tech mapping (new entry): `nuclear_smr→1.0`,
`hydrogen_ct/ccgt→1.0`, `wind/solar/geothermal/offshore_wind→1.0`, and `gas_cc_ccs` →
capture fraction (clean_capture) or CESA formula on residual class CI (cesa_ci);
others 0.

### 5.2 New module `src/market_sim/policy/federal_ces.py`

```python
premium_for_year(config, year) -> float          # 0 unless enabled; knots or base×(1+esc)^n
unit_credit_fractions(config, fleet) -> np.ndarray   # (n_gen,), vectorized (rule 2):
    # clean_capture: eligible zero-carbon mask ×1.0; gas_cc_ccs → ccs_capture_fraction;
    #                unabated fossil → 0.
    # cesa_ci:       eligible fuels → clip(1 − emission_rate/benchmark, 0, 1);
    #                + unabated gas_cc with emission_rate ≤ 0.45 → same formula;
    #                emission_rate in t/MWh at the LP boundary.
tech_credit_fraction(config, tech) -> float      # candidate-tech table above
effective_eac_price_for_tech(config, tech, year) -> float
    # max(get_eac_price_for_new_entry(tech, config), premium_for_year × tech_credit_fraction)
effective_unit_eac_prices(config, fleet, year) -> np.ndarray
    # max(legacy per-fuel scalar broadcast, premium × unit_credit_fractions)
```

Unit tests first at trivial scale (1 gen / 24 h — repo testing pattern), including:
disabled ⇒ all-zeros & legacy pass-through; escalation vs knots; both crediting modes
(capture fraction; CESA clipping; the 0.45 eligibility line incl. a unit just above it);
str-key coercion; backcast guard.

### 5.3 Consumer wiring (W2-A; exact seams — retrofit seam EXCLUDED pending §11)

| Seam | Site | Change |
|---|---|---|
| Thermal dispatch MC | `runner.py:1094` → `eac.py:43` | `apply_eac_to_mc(mc, fleet, config, year)`: subtract `effective_unit_eac_prices` (covers nuclear/ccs/geo/osw + hydro/hydrogen + cesa_ci unabated-CCGT fractions; hydro ≈ dispatch-inert, harmless) |
| Wind/solar/storage credits | `runner.py:1141` → `eac.py:83` | `compute_eac_dispatch_credits(config, year)`: `max(legacy, premium×1.0)`; storage only if `federal_ces_storage_eligible` |
| Retirement screen | `capacity.py:1418` | effective price via `effective_eac_price_for_tech(..., year)` — under `cesa_ci`, credited unabated gas_cc also earns its fraction here; 45U `max()` fold unchanged |
| New entry (emerging + classic) | `capacity.py:2229-36, 2399-2406` | replace inlined `max()` with resolver → **nuclear_smr & hydrogen now earn the premium** |
| CCS retrofit screen | `capacity.py:2838-2981` | **DEFERRED to W2-C** (§11). Until then the retrofit screen keeps its legacy `eac_price_ccs` input only — campaign runs do not start before W2-C lands (D9 gate anyway). |
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
   (wind: −PTC−premium; nuclear/CCS: mc−premium×fraction). In surplus hours the marginal
   credited MWh sets prices as low as its negative keep-running value, so the premium
   *deepens* negative/zero-price epochs as penetration grows — the real CES/PTC dynamic.
   The existing dump-cost guard already prevents credit-farming of curtailed energy
   (objective: `dump_cost = max(ε, −min(wind_mc, solar_mc)+ε)`).
2. **Delivered-only payment**: premium revenue accrues to *dispatched* MWh. Curtailment
   erodes premium capture automatically; the premium-capture-rate metric reports it.
3. **Price cannibalization**: captured energy price by tech = dispatch-weighted LP duals,
   which fall in clean-heavy hours as buildout proceeds. Total unit revenue = captured
   price + premium + (capacity/AS where applicable) — reported per plant.
4. **Capacity-evolution feedback**: entry proceeds while premium-inclusive margin clears
   the screen; each ladder case runs the full one-pass evolution 2026→2050, so
   saturation, storage response, retirements and CCS retrofits equilibrate per premium
   level. The ladder therefore traces the **clean-share-vs-premium response surface**
   (and its inverse: the premium needed for a target clean share), with
   `entry_screen_diagnostics` recording exactly how much the premium moved each
   candidate's margin each year.

## 7. Capacity-screen readiness gate (owner decision D9 — fix BEFORE running)

The forecast retirement/entry screens are the model's documented weak frontier
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md`, lane mostly OPEN):
capacity-market ISOs economically retire ≈ nothing (payment clears 1.26–4.92× FOM —
PJM), ERCOT over-retires ~15× (22.8 vs 1.5 GW, 96% false-retire; no in-year scarcity
formation in the screen), and **solar new entry is zero in both ISOs against 25.1 / 13.1
GW actuals (BLK-8)**.

**Owner decision:** no campaign until these are fixed. The fixes belong to the
already-chartered retirement-calibration lane (its own plan doc, ordered steps F-0…F-9,
owner-ordered Opus/Fable-only) — this plan does NOT fork that work; it defines the
**CES-readiness criteria** the lane must satisfy before W4 launches:

- **R1 (VRE entry — blocks everything):** BLK-8 resolved — BAU forecast builds
  materially nonzero solar (and wind) in ERCOT and PJM, validated against the lane's own
  hindcast acceptance (ERCOT ~25 GW-class, PJM ~13 GW-class solar through the hindcast
  window, within the lane's tolerance).
- **R2 (ERCOT exits):** economic-retirement over-fire corrected to the lane's hindcast
  acceptance (screen scarcity/AS revenue basis fixed; false-retire rate collapses from
  96%).
- **R3 (PJM exits):** capacity-market clearing calibration (RC-1A probe → position
  basis) landed so fossil economic exit is arithmetically possible in capacity-market
  designs.
- **R4 (regression):** `tests/golden/ercot_2026_2040.json` (or its successor) green;
  `check_forecast_invariants.py` I1-I14 pass on fresh ERCOT+PJM BAU forecasts.
  *W1-B finding: R4 is structurally unachievable for PJM until G10 (W2-D) lands — the
  I7 FAIL is adequacy-accounting, not fleet economics. W3-R treats W2-D as an R4
  prerequisite. ERCOT already passes 14/14 on the 2026 smoke.*

**W3-R verification session** (§8) independently re-runs both BAU forecasts, checks
R1-R4, and issues the go/no-go for W4. Until then, W1/W2 build work proceeds — none of
it depends on the screens.

## 8. Build plan — waves of parallel session prompts

Waves run **sequentially**; prompts within a wave are **independent parallel sessions**
(disjoint files). Every session: start from latest `origin/main`; push via
`mcp__github__push_files` only (never `git push`; verify any pushed file ≥300 lines);
NO new GitHub Actions workflows; NO solves on CI runners. Core-infrastructure sessions
(`src/market_sim/`, `scripts/run_*/score_*`, spec, workflows) are **Opus/Fable only**
(rule 27); W1-C is the only Sonnet-eligible prompt. Each prompt is self-contained and
cites this plan (§ references).

### Wave 1 (parallel: W1-A, W1-B, W1-C) — ✅ COMPLETE, merged to main 2026-07-17
(W1-A PR #2378: config surface + resolver + tests. W1-B PRs #2371/#2379: four YAMLs +
smoke report — ERCOT 14/14 PASS, 172.7 s / 3.63 GB; PJM first-ever forecast run,
12 PASS / I7 FAIL (→ G10) / I12 WARN (derivative), 380.4 s / 8.73 GB. W1-C PR #2375:
crediting audit. Findings promoted to G10-G12; capture-fraction 0.95 flip → W2-A
task 0.)

**W1-A — Core config surface + `policy/federal_ces.py` resolver (Opus/Fable)**
Implements §5.1 + §5.2 ONLY (no consumer wiring — solver-inert by construction), with
the v2 crediting modes (`clean_capture` default / `cesa_ci` variant, capture fraction
0.95, 0.45 eligibility line). Acceptance: full G8 registration checklist; unit tests
incl. neutrality (`federal_ces_enabled=False` ⇒ zeros/legacy pass-through, cache_key
unchanged at defaults via `_CACHE_KEY_OPTIONAL_FIELDS`); backcast guard raises;
`pytest tests/` green; `python scripts/validate_parameters.py` green.

**W1-B — ERCOT + PJM forecast-BAU readiness smoke (Opus/Fable)**
Creates `configs/scenarios/{ercot,pjm}_ces_base_2026_2050.yaml` (mode: forecast,
`entry_screen_diagnostics: true`) + 2026-only smoke variants; runs both 1-year BAU
smokes in-session; runs `check_forecast_invariants.py`; documents PJM blockers (there is
no committed PJM forecast config today — expect issues) in
`docs/handoffs/ces-w1b-bau-smoke-2026-07.md`. Fix-forward only trivial config-level
issues; report (don't fix) anything structural.

**W1-C — Crediting input audit (Sonnet-eligible; additive docs only)**
Audits per-plant forward CO2-rate coverage for ERCOT+PJM fleets (measured vs
`class_fallback`; unit check t/MWh), computes credit-fraction distributions by fuel
under BOTH v2 modes (incl. the 0.45 line: which existing/announced CCGTs clear it),
reconciles `federal_ces_ccs_capture_fraction` vs the engineering
`ccs_capture_rate`/`ccs_retrofit_capture_rate` fields, finalizes citations (CESA
S.1359/S.2146 for 0.82; EPA §111(b) 1,000 lb CO2/MWh correspondence for 0.45) +
`parameters.json` drafts, and sanity-checks ladder {10,20,30} against
`EAC_PRICE_REFERENCE` + scope2 breakevens. Deliverable:
`docs/handoffs/ces-ci-crediting-audit-2026-07.md`.

### Wave 2 (W1 complete. Launch W2-A ∥ W2-B ∥ W2-D in parallel — disjoint files;
W2-E in parallel once the owner approves its approach; **W2-C AFTER W2-A merges** —
both touch scenarios.py/capacity.py/spec, and W2-C reuses W2-A's wired resolver)

**W2-A — Consumer wiring EXCLUDING the retrofit seam (Opus/Fable)**
**Task 0 (owner Q4 catch-up):** flip `federal_ces_ccs_capture_fraction` default
0.90 → 0.95 (scenarios.py:267 + comment; tests/test_federal_ces.py:252-260 default
assertion and :370 tech-fraction assertion; `frontend/data/parameters.json`
`scenario.federal_ces_ccs_capture_fraction` entry + regenerated citations page) — W1-A
merged before the Q4 decision. Then:
implements §5.3 (retrofit row deferred), incl. the `nuclear_smr`/`hydrogen` candidate
mapping and cesa_ci unabated-CCGT crediting through dispatch + retirement + entry.
Read `docs/handoffs/ces-ci-crediting-audit-2026-07.md` first (production-path and
provenance findings shape the wiring).
Neutrality golden: CES-off run byte-identical vs main. Integration tests: premium moves
entry margins/retirement retention in trivial fixtures; year-escalation visible across
two solved years; cesa_ci credits an efficient CCGT and zeroes an inefficient one.
Updates `model-methodology-spec.md` (§1.4 + §5.x: EAC mechanism, max() rule, federal CES
layer — closes G7).

**W2-B — Reporting & comparison harness (Opus/Fable)**
Implements §5.4: `plant_financials.py` attribute line, `_summarize_year` +
`_SCALAR_METRICS` additive metrics, `scripts/report_ces_campaign.py`,
`configs/ces_premium_matrix.yaml` (first-campaign cases: `BAU: {}` + `CES-10/20/30`,
all `clean_capture`) plus a PARKED `configs/ces_premium_matrix_ci.yaml`
(`CI-10/20/30`, `cesa_ci`) so the efficient-CCGT option is turnkey when the owner calls
it. Tests on synthetic cached fixtures.

**W2-C — CCS-retrofit redesign (Opus/Fable; §11 FULLY RESOLVED 2026-07-17 — launch AFTER W2-A merges)**
Implements the §11 resolution: 45Q revenue term in the retrofit screen, annualized over
`min(ira_45q_credit_window_years, remaining_life)` and expiry-gated, with
`ira_45q_credit_window_years: int | None = 12` (None ⇒ indefinite — owner-requested
option; default 12 per statute) applied consistently to the NEW-BUILD CCS LCOE too
(flag: a behavior change to new-build CCS economics); screen revenue basis moved from
the fixed 0.55 CF to prior-year attainable margin **at the post-retrofit cost basis**
(HR penalty + VOM adder in, 45Q and premium×fraction as bid offsets) so anticipated
utilization is endogenous; premium enters as `max(eac_price_gas_cc_ccs,
premium × capture-fraction credit)` with 45Q stacking on top; capture crediting at
0.95; **the joint three-way choice** (§11 final block): retirement and retrofit
evaluated together for retrofit-eligible gas-CCs — retire only if unabated AND retrofit
continuations both fail, retrofit valued as the INCREMENTAL uplift over the best
unabated state (which under cesa_ci includes the unit's unabated partial credit),
3 GW/yr cap honored with cap-displaced units falling back to the unabated path/loss
counter, annual re-screen from `ccs_available_year`, still one pass (rule 10) — the
evolve_fleet step order/spec §5.1 documentation updated accordingly; refreshed
parameter citations. Includes retrofit-specific tests + spec §5.6 rewrite.

**W2-D — PJM adequacy side-registry intake (Opus/Fable; closes G10, prereq for §7 R4)**
Data/constants intake with primary citations: PJM BRA planning parameters — DR /
load-management UCAP contribution (→ `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]`
or an absolute-MW analog if the fraction form misfits, documented per rule 14) and CIL
firm-import treatment (→ `ADEQUACY_EXTERNAL_TIE_FIRM_MW["PJM"]`), consumed at
capacity.py:870 / :2656. Values must be published PJM parameters (cited in
`parameters.json`) — NEVER tuned to clear I7 (rules 5/13; W1-B B1 quantifies the 5,439
MW gap the published DR fleet more than covers). Acceptance: PJM 2026 smoke re-run
passes I7/I12; ERCOT bytes untouched.

**W2-E — Forecast-mode hygiene fixes (Opus/Fable; owner-approved approach; closes
G11 + G12 hardening)**
APPROVED: mode-gate (Option 1), owner 2026-07-17.
(a) Mode-gate the F923 plant-monthly fuel overlay to backcast (recommended; the
alternative clamp `available_years < resolved start_year` in forecast mode is the
fallback if the owner prefers year-based semantics) — flag in the PR that any 2026+
forecast bytes change (golden regen note). (b) Fail loudly when
`confirmed_exits_enabled` is on in forecast mode and the clean registry cannot be
read/imported (W1-B B4) instead of the silent 477 MW warn-only no-op. Tests for both.

### Wave 3 — capacity-screen readiness (external lane + verification)

The retirement-calibration lane executes under its own plan
(`forecast-retirement-calibration-plan-2026-07.md` F-0…F-9; Opus/Fable-only per owner
order). This plan contributes exactly one session:

**W3-R — CES-readiness verification (Opus/Fable)**
Re-runs ERCOT + PJM BAU forecasts (2026-2050) on then-current main; evaluates §7 R1-R4
with evidence (ledger build/retire tables vs lane acceptance, invariants, goldens);
writes `docs/handoffs/ces-w3r-readiness-2026-XX.md` with an explicit GO / NO-GO (and,
if NO-GO, the blocking item list). W4 may not launch without a GO.

### Wave 4 — campaign (BLOCKED on W3-R GO)

**W4-A / W4-B — ERCOT / PJM premium-ladder campaigns**
`market-sim matrix --config configs/scenarios/<iso>_ces_base_2026_2050.yaml
--matrix configs/ces_premium_matrix.yaml` in-session (background bash; per-year caching
makes interrupts resumable; years always sequential; ≤2 solves in flight TOTAL across
both sessions — rule 12: run the two ISOs' matrices with `--workers 1` each in parallel,
or sequentially with `--workers 2`). 4 legs/ISO (BAU + {10,20,30}, `clean_capture`) ×
25 years; recorded timing implies ~4-5 h/leg — plan ~8-10 h wall per ISO at
2-concurrent. (The parked `cesa_ci` ladder adds 3 legs/ISO whenever the owner calls it.)
Gate every case with `check_forecast_invariants.py` (+ paired CES-vs-BAU direction
check); `generate_financial_reports.py` per case; `report_ces_campaign.py`; commit the
matrix bundle + report doc (§7 caveat context included).

**W4-C — Synthesis + docs**
Cross-ISO synthesis memo (clean-share-vs-premium curves by crediting mode, revenue
decomposition by plant/company, retrofit/new-build attribution, cannibalization
metrics), owner review, `/sync-docs`.

### Wave 5 (optional, owner call)
Endogenous ISO-level CES constraint (CI-weighted `_build_rps_row` generalization + ACP
analog) as a cross-check of the exogenous ladder; premium as a PB-2 sampler dimension or
`policy_bundle` extension (`resolve_policy_bundle` doesn't touch `eac_price_*` today).

## 9. Rule-compliance checklist

- Rule 22 quarantine: forecast-mode 2026+ only; no measured H1-2026 actuals anywhere —
  unrestricted. Backcast guard makes the lever un-usable as a backcast tuning channel
  (rule 13).
- Rule 24 (no off-registry knobs): every parameter is a ScenarioConfig field in
  `TIER_TAGS` + `parameters.json`; one delivery channel (ERCOT-65 lesson).
- Rule 5 / citations: benchmark 0.82 (CESA S.1359/S.2146), threshold 0.45 (EPA §111(b)
  correspondence, W1-C finalizes), capture fraction 0.95 (owner simplification — target
  capture rate; 0.90 sensitivity), 45Q window 12 yr (26 U.S.C. §45Q(a)(3)-(4)), plus the
  NY ZEC / PJM GATS ranges already in `EAC_PRICE_REFERENCE`.
- Rules 2/6: credit fractions vectorized over the fleet arrays; no hour loops.
- Rule 27: core sessions Opus/Fable; push_files with ≥300-line verification.
- Rules 15/16 (backcast dashboard) do not govern forecast campaigns; W4 deliverables are
  committed matrix bundles + reports under `results/ensemble/` + `docs/handoffs/`.
- CLAUDE.md CI policy: all solves in-session; no per-task workflows.

## 10. Owner decision register — RESOLVED 2026-07-17

1. Crediting → two modes (D1): `clean_capture` default; `cesa_ci` variant with 0.45
   t/MWh unabated-CCGT line; assumed capture 0.95 (owner: target rate; 0.90
   sensitivity). **First campaign runs `clean_capture` only; `cesa_ci` is a built
   option** (owner 2026-07-17). *Implementation note: W1-A merged with 0.90 (launched
   pre-Q4); the 0.95 flip is W2-A task 0.*
   *Pending micro-check: 0.45 as eligibility cutoff (assumed) vs as formula denominator
   — W1-A implemented the cutoff reading; W1-C audit §2.5 restates the flag.*
2. Existing clean credits identically — confirmed (no vintage gate).
3. Horizon 2026–2050; first-run ladder {10, 20, 30} — confirmed.
4. Escalation 0%/yr real — confirmed.
5. Storage discharge not credited — confirmed.
6. CCS retrofit → design discussion FULLY RESOLVED 2026-07-17 (§11); W2-C implements.
   45Q stacks; 12-yr window w/ indefinite option; no fixed CF — economics-based
   utilization; capture 0.95; Q5 closed (interim = leave legacy; campaign gated);
   PLUS the joint retrofit-vs-retire three-way choice with incremental economics
   (owner's framing — see §11 final block).
7. Screens fixed before meaningful runs — confirmed (D9; §7 gate; W3-R go/no-go).

## 11. CCS-retrofit treatment — design discussion (for owner resolution)

**Current mechanics** (`apply_ccs_retrofit`, capacity.py:2838-2981): screens existing
gas-CC with ≥15 y remaining life, capped 3 GW/yr/ISO, gated `ccs_available_year` (2030).
Simple payback: `capex / (carbon_avoided + eac_price_ccs·CF·8760 − HR-penalty margin
loss − VOM adder)` vs remaining life, at a **fixed screen CF of 0.55**
(`_RETROFIT_SCREEN_CF`, :215). Retrofit flips `fuel_type → gas_cc_ccs` (:2972) — the
unit then automatically earns CCS dispatch credits and retirement-screen attribute
revenue in later years. Capture/HR/VOM via `ccs_retrofit_capture_rate` /
`ccs_retrofit_hr_penalty` / `ccs_retrofit_vom_adder`. **No 45Q anywhere in the retrofit
screen** (new-build CCS LCOE has it, :2742).

**Defects/simplifications to resolve:**
1. **45Q absence.** Statutory $85/t × captured t/MWh ≈ high-$20s/MWh — the dominant
   real-world retrofit driver. With it missing and `eac_price_ccs=0`, BAU retrofits are
   ~impossible for the wrong reason, so ANY premium-case retrofit is mis-attributed to
   the premium. Also note 45Q is a **12-year credit window** from placed-in-service,
   gated by `ira_ccus_45q_last_year` — a payback screen that ignores the window
   overstates late-life retrofits.
2. **Fixed 0.55 CF revenue basis.** The screen ignores the unit's own economics; under a
   premium the unit would run MORE (it bids premium-lower), so a static CF understates
   the premium response. The retirement screen already uses attainable inframarginal
   margin from prior-year duals — the structurally consistent basis (rule 1).
3. **Undiscounted payback vs remaining life** while new entry uses LCOE/margin
   economics — asymmetric hurdle.
4. **Capture-rate field duplication**: engineering `ccs_retrofit_capture_rate` vs
   new-build `ccs_capture_rate` vs the new policy-assumed
   `federal_ces_ccs_capture_fraction` — needs one documented relationship (W1-C reports
   current values).
5. **Stacking**: premium (certificate) + 45Q (tax credit) + carbon price (avoided cost)
   are three distinct instruments that DO coexist in reality; the model must document
   that the retrofit sees all three without double-counting any single tonne twice
   within one instrument.
6. **Not modeled (acknowledge, don't build now):** CO2 transport/storage geography
   (Gulf-Coast ERCOT favorable vs heterogeneous PJM), FEED/outage time, the 3 GW/yr/ISO
   cap's provenance.

**RESOLUTION (owner, 2026-07-17 — Q1–Q4 answered; Q5 pending):**
- **Q1 — RESOLVED: 45Q stacks with the premium** (certificate ≠ tax credit). Retrofit
  attribute term = `max(eac_price_gas_cc_ccs, premium × capture-fraction credit)`,
  45Q added on top as its own statutory revenue term.
- **Q2 — RESOLVED: model the 12-year credit window, with an indefinite option.** New
  field `ira_45q_credit_window_years: int | None = 12` (statutory default; `None` ⇒
  credit runs for remaining life — owner-requested extension scenario). Annualize over
  `min(window, remaining_life)`, gated on `ira_ccus_45q_last_year` at the retrofit
  year. Apply the same window to the NEW-BUILD CCS LCOE for consistency (flagged: a
  behavior change to new-build CCS economics — today it credits 45Q un-windowed).
- **Q3 — RESOLVED: no fixed CF anywhere.** The 0.55 was a legacy screening shortcut for
  expected utilization inside the payback formula (post-retrofit DISPATCH was always
  endogenous). Owner: "let them run how it makes sense economically." The screen's
  revenue basis becomes the unit's attainable inframarginal margin over the prior
  year's hourly prices AT THE POST-RETROFIT COST BASIS (heat-rate penalty + VOM adder
  in; 45Q $/MWh and premium×fraction as bid offsets) — so the screen anticipates the
  near-baseload 45Q-driven utilization the owner describes (80-90 % CF emerges when
  post-retrofit effective cost clears the price duration curve that deep), consistent
  with the retirement screen's construction (rule 1).
- **Q4 — RESOLVED: 0.95** assumed capture for crediting (the target capture rate);
  0.90 kept as a labeled sensitivity. `federal_ces_ccs_capture_fraction = 0.95`.
- **Q5 — RESOLVED (closed 2026-07-17): leave legacy behavior in the interim.** The
  question was only about throwaway diagnostic runs while W2-C is being built; the
  campaign is gated on §7 regardless, so nothing meaningful runs on the legacy screen.
  No freeze, no `ccs_available_year` bump.

**Joint retrofit-vs-retire choice (owner 2026-07-17 — surfaced by the Q5 exchange; a
hard W2-C requirement):** "CCGT plants will have a choice between retrofit or retire
they will need to make when faced with it under these economic conditions with a CES,
or they may go retrofit sooner if it's more profitable than staying unabated."
Today's `evolve_fleet` order cannot express this: economic retirement (step 2) runs
BEFORE the retrofit screen (step 4), so a loss-making CCGT exits without ever being
offered the retrofit. W2-C makes the decision joint for retrofit-eligible gas-CCs,
inside the existing single pass (rule 10 — ordering/joint evaluation, no iteration):
- Value three continuations per unit-year: **stay unabated** (going-forward margin,
  incl. any `cesa_ci` partial credit the unit earns unabated), **retrofit** (post-
  retrofit attainable margin + 45Q + premium×capture-credit − annualized retrofit
  capex/costs), **retire** (zero).
- **Retire only if BOTH continuations fail** the unit's threshold (loss-year counter
  semantics preserved); **retrofit when it beats staying unabated AND clears the
  payback-vs-remaining-life hurdle** — which, with 45Q + premium at near-baseload
  post-retrofit utilization, can trigger well before distress ("retrofit sooner if
  more profitable than staying unabated").
- Retrofit value is the **incremental uplift over the best unabated state** — under
  `cesa_ci` that nets out the unabated partial credit (uplift ≈ premium×(0.95−f_unabated)
  + 45Q − costs); under `clean_capture` the unabated credit is 0 and the full
  premium×0.95 + 45Q is the uplift. No gross-vs-incremental double count.
- The **3 GW/yr/ISO cap** stays: cap-displaced would-be retrofits fall back to the
  unabated path and the normal loss-year counter (they may retire in a later year if
  unabated keeps failing and the cap keeps binding).
- Spec §5.1 step-order documentation updated to reflect the joint evaluation.

Superseded design notes kept for the record: (d) payback-vs-remaining-life stays the
criterion (simplicity; documented asymmetry vs new entry), (e) the 3 GW/yr cap +
availability year stay (cite or flag the cap).
