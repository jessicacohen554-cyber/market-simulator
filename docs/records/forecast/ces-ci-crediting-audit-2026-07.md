# CES CI-Crediting Input Audit — W1-C (2026-07)

**Status:** COMPLETE — read-only data audit, no model code touched, no LP solved.
**Session:** Wave 1-C of the national CES EAC-premium plan
(`docs/handoffs/national-ces-eac-premium-plan-2026-07.md` **v2**, commit `1e10c85` on
`claude/national-ces-eac-premium-xoadma`; v1 `d6b7455` is what main carries at this
writing). Scope per plan §8 W1-C: audit the crediting inputs for the two v2 crediting
modes (§1 of the plan), reconcile the capture-rate knobs (§11 item 4), finalize the
citation packet + `parameters.json` drafts (§5.1), and sanity-check the first-run
ladder {10, 20, 30}.
**Method:** the ERCOT and PJM 2026 forecast base fleets were built in-session with the
production builders (`ScenarioConfig(iso=…)` defaults → `load_or_synthesize_bins` →
`build_base_fleet` at year 2026, planned EIA-860 additions and confirmed exits applied,
`apply_plant_emission_rates_v2` re-applied exactly as `build_dispatch_fleet` does
per-year). No dispatch was solved; every number below is a fleet/input property, at
repo state `e1fcb02` (origin/main, 2026-07-17).

## TL;DR — findings that change what W1-A/W2-A/W2-C should do

1. **CITATION CORRECTION (plan §1/§5.1/§9).** The 0.82 t CO2e/MWh benchmark is
   **Bingaman S.2146 (112th Cong., 2012) §610(f)(1)** — NOT S.1359. **CESA S.1359
   (116th Cong., 2019, Smith) uses a 0.4 t CO2e/MWh benchmark** (§610(b)(1)) with the
   same `1 − CI/benchmark` construction (§610(f)(1)). Verified from the govinfo bill
   texts (§4 below). The plan's "CESA S.1359 116th Cong.; Bingaman S.2146 112th"
   pairing for 0.82 must be re-anchored: **cite S.2146 for the 0.82 number**, cite
   S.1359 as the modern design precedent for fractional crediting (its stricter 0.4
   benchmark is a natural future sensitivity, not the default).
2. **Coverage is strong — `cesa_ci` stands on measured ground.** 88.4% of ERCOT and
   92.8% of PJM fossil MW (≈90% and ≈99% of estimated fossil energy) carry
   CAMPD/CEMS-measured trailing-average CO2 rates at the LP boundary; gas-CC
   specifically is 89.1% (ERCOT) and 99.7% (PJM) measured by MW. Unit convention
   confirmed: tonnes CO2 per net MWh everywhere at the boundary (§1).
3. **Measured-vs-fallback barely moves the fleet-average crediting but redraws the
   0.45 boundary — and the fallback's error is one-sided toward over-crediting
   cogens.** Against the true production fallback (the v2-off fleet:
   `get_emission_rate(fuel, base_hr)`, the plant's *physical* heat rate), the
   capacity-weighted `cesa_ci` fraction of the CC fleet moves ≤0.012 in both ISOs,
   but 2.4 GW (ERCOT) / 5.1 GW (PJM) of plant capacity flips eligibility. The
   dominant flip direction is OUT: 0.7 + 3.5 GW of CHP/duct-fired capacity (Morris,
   Hunterstown, Ironwood, Hopewell, Deer Park, …) that the HR default would credit
   at CI 0.32-0.44 books measured CIs of 0.51-0.73 — all stack CO2 over net electric
   MWh — and is correctly refused. `cesa_ci` must run on the v2 measured rates; the
   residual risk is the CEMS-**uncovered** CC capacity (ERCOT 4.1 GW, mostly
   industrial cogens) that only has the flattering HR-default CI available (§2.3,
   owner item O-3).
4. **The production fallback is NOT `class_median_rates`.** At the LP boundary,
   v2-uncovered units carry physical-HR × EPA fuel factor
   (`get_emission_rate`, fleet.py:7171-7178). The estimator's class-median fallback
   (plan §2.1 step 4 / the `class_fallback` provenance flag of
   `forward_plant_co2_rate`) is wired only into the LOYO harness
   (`scripts/loyo_co2_rates.py`) and tests — no production consumer. W1-A's
   `unit_credit_fractions` reads `fleet.emission_rate`, so it inherits the HR-default
   bucket, not a class-median bucket (§1.3).
5. **Three capture knobs, three roles, one number.** `ccs_capture_rate` (new-build,
   scenarios.py:411, **uncited**), `ccs_retrofit_capture_rate` (retrofit,
   scenarios.py:430-431, NETL amine basis), and the citation-bearing but **dead**
   `CCUS_PARAMS["gas_cc_ccs_90"]["capture_rate"]` (constants.py:4203, NETL 2022 Case
   B31B) are all 0.90. The proposed `federal_ces_ccs_capture_fraction` (0.90/0.95) is
   a *policy crediting* assumption layered on top; at 0.95 it credits more capture
   than the engineering fields produce, and under `cesa_ci` it is **inert by
   construction** (that mode reads the unit's residual CI, crediting ≈0.947-0.956 at
   90% engineering capture — more generous than `clean_capture`'s 0.90). §3 gives the
   reconciliation table and a recommended validation rule.
6. **Ladder {10, 20, 30} real 2026$/MWh is sane and well-shaped** against both
   `EAC_PRICE_REFERENCE` (constants.py:4786-4801) and the scope2-lce-portfolio prior
   art: $10 ≈ existing-clean attribute territory, $20 ≈ the illustrative new-build/CCS
   breakeven frontier, $30 deliberately supra-breakeven (above everything except
   offshore-wind ORECs at 20-40). No rung is redundant; no rung is absurd (§5).

Open items for the owner are collected in §6.

---

## 1. Forward CO2-rate coverage — ERCOT + PJM forecast fleets

### 1.1 What is being measured

`cesa_ci` credits per-unit as `f = clip(1 − CI/0.82, 0, 1)` with the unabated-CC
eligibility line at CI ≤ 0.45 t/MWh, where CI is the unit's forward CO2 rate at the
LP boundary. This section audits where that CI comes from, per plant, for the 2026
forecast fleets.

**Unit convention — confirmed.** The model's canonical emission-rate unit at the LP
boundary is **tonnes per net MWh** for every pollutant. The kg→tonnes conversion is
documented at `data/emission_rates.py:250-253` ("converted kg/MWh → tonnes/MWh at the
boundary (the model's canonical unit for every emission rate — CO2, NOx, SO2 alike)")
and enacted at `emission_rates.py:306` (`… / net / 1000.0` inside
`measured_plant_rates`); the legacy pooled-artifact path divides by
`_KG_PER_TONNE = 1000.0` (fleet.py:7528, used :7552-7554). Downstream, dispatch MC
consumes `emission_rate × carbon_price` with carbon prices in $/tonne, so the
`cesa_ci` thresholds (0.82 / 0.45 t/MWh) compare like-for-like with
`fleet.emission_rate` with no further conversion. Note the basis is **net** MWh and
**stack CO2 only** — relevant caveats vs the statutes' CO2e constructions in §4.

### 1.2 The production path (what a CES resolver will actually see)

- The mode-aware source is the v2 artifact (`plant_emission_rates_v2.parquet`,
  `use_plant_emission_rates_v2=True` default since G-39, scenarios.py:540-543).
  In **forecast** mode `measured_plant_rates` (emission_rates.py:261-307) books the
  gen-weighted trailing average over the last `CO2_RATE_TRAILING_WINDOW_YEARS = 2`
  years of history (constants.py:403) — the estimator base (a) of
  `forward_plant_co2_rate` — keyed `(plant_id, coarse fuel_class)` with the
  unit-composition mask.
- For ERCOT/PJM the artifact holds plant-years 2018-2021 + 2023-2025 (no 2022 —
  validation-holdout year; no 2026 rows for these ISOs), so **the 2026-forecast
  trailing window is [2024, 2025]**.
- The override lands on the fleet twice, identically: inside `bins_to_fleet`
  (fleet.py:9770-9778, the G-39 §9.6 both-paths fix) and per-year in
  `build_dispatch_fleet` (fleet.py:10238-10247). Only positive measured rates
  override (`apply_plant_emission_rates_v2`, fleet.py:7673-7675) — a plant/class with
  no measured CO2 mass keeps its default.
- **The default (fallback) for v2-uncovered units** is the plant's **physical** heat
  rate (`base_hr` from the bin sheet / registry annual HR, group default when absent
  — `_fill_plant_hr`, fleet.py:7728-7737; deliberately NOT the bid-tranche HR with
  its offer-curve pricing multipliers, per the R2/EM-4 comment at
  fleet.py:9708-9727) × `FUEL_CO2_FACTOR_PER_MMBTU` (constants.py:369-376: gas
  0.057, coal 0.100, oil 0.074, **biomass 0.0** — biogenic carbon-neutral by
  EPA/RGGI accounting) via `get_emission_rate` (fleet.py:7171-7178).

### 1.3 Provenance-bucket finding: the "class-median fallback" does not reach the LP

`forward_plant_co2_rate` (emission_rates.py:155-228) labels its output
`trailing_avg` | `nn_conditioned` | `class_fallback`, and plan §2.1 step 4 assigns
CEMS-uncovered plants and new entrants the gen-weighted class (plant_group × fuel)
median (`class_median_rates`, emission_rates.py:310-343,
`CO2_RATE_CLASS_MEDIAN_PERCENTILE = 50.0`, constants.py:417). **Grep-verified: no
production caller.** `class_median_rates` and `forward_plant_co2_rate` are consumed
only by `scripts/loyo_co2_rates.py` (the frozen LOYO harness) and
`tests/test_emission_rates.py`; the fleet path uses `measured_plant_rates` (the same
base-(a) estimator) and falls back to HR × fuel factor, never to the class median.
The NN-conditioning refinement (b) is likewise inert in production
(`CO2_RATE_CONDITIONING_ENABLED = False`, constants.py:429).

So at the LP boundary the three provenance buckets the audit was asked to quantify
resolve as:

| bucket | what it actually is in production | flag analogue |
|---|---|---|
| measured | (plant, fuel-class) trailing-avg over [2024, 2025] CEMS | `trailing_avg` |
| fallback | physical-HR × EPA fuel factor (NOT the class median) | (`class_fallback` never fires in the fleet path) |
| zero | biomass (biogenic 0 by design) + nuclear/renewables (CI 0) | — |

This is not a defect for `clean_capture` (CI-blind), and for `cesa_ci` it is
quantified below — but W1-A should document that `unit_credit_fractions` inherits
this fallback, and the owner may want uncovered *credited* units (cogens) pushed to
the class median instead (§6 O-3).

### 1.4 Coverage tables

Capacity = fleet `pmax` (2026 base fleet incl. planned units due ≤2026; ERCOT: 2
confirmed-exit rows, 477 MW, removed; PJM: 8 confirmed exits on file are all
post-2026). Energy weights: covered plants use their trailing-window mean annual
measured net MWh; uncovered plants are estimated at pmax × 8760 × the measured class
CF of covered same-class plants (ERCOT: coal 0.50, CC 0.59, CT 0.20, ST 0.16; PJM:
coal 0.39, CC 0.64, CT 0.12, ST 0.14, oil 0.07) — an audit construction, not a model
output. Nuclear/biomass energy is not estimated (no CEMS energy basis; CI is 0 by
design for both, so CO2-rate "coverage" is not meaningful there).

**ERCOT (633 fleet units, 78.5 GW incl. 4,980 MW nuclear; 296 units v2-overridden):**

| fuel | units | MW | MW measured | % MW measured | est TWh/yr | % energy measured |
|---|---:|---:|---:|---:|---:|---:|
| coal | 40 | 13,964 | 13,964 | 100.0 | 60.67 | 100.0 |
| gas_cc | 160 | 37,241 | 33,171 | 89.1 | 193.3 | 89.1 |
| gas_st | 50 | 11,296 | 9,026 | 79.9 | 15.73 | 79.9 |
| gas_ct | 379 | 10,971 | 8,753 | 79.8 | 20.44 | 79.8 |
| nuclear | 4 | 4,980 | 0 | 0.0 | n/a | n/a |
| **fossil total (excl. biomass)** |  | **73,473** |  | **88.4** |  | **90.2** |

**PJM (1,858 fleet units, 170.7 GW incl. 33,492 MW nuclear; 622 units v2-overridden):**

| fuel | units | MW | MW measured | % MW measured | est TWh/yr | % energy measured |
|---|---:|---:|---:|---:|---:|---:|
| coal | 148 | 35,433 | 33,612 | 94.9 | 119.79 | 99.7 |
| gas_cc | 248 | 59,719 | 59,551 | 99.7 | 335.85 | 99.7 |
| gas_st | 110 | 9,490 | 7,558 | 79.6 | 11.56 | 83.6 |
| gas_ct | 411 | 26,392 | 24,093 | 91.3 | 27.03 | 92.1 |
| oil | 389 | 4,424 | 2,464 | 55.7 | 2.76 | 59.6 |
| biomass | 520 | 1,745 | 0 | 0.0 | n/a | n/a |
| nuclear | 32 | 33,492 | 0 | 0.0 | n/a | n/a |
| **fossil total (excl. biomass)** |  | **137,204** |  | **92.8** |  | **98.7** |

Reading: every ERCOT coal MW and 99.7% of PJM gas-CC MW is on measured rates; the
uncovered tail is small-CT/cogen capacity that runs little (energy coverage ≥ MW
coverage everywhere except flat classes). The zero-rate bucket at the LP boundary is
exactly PJM's 1,745 MW biomass (biogenic zero, `FUEL_CO2_FACTOR_PER_MMBTU["biomass"]
= 0.0`) — no fossil unit carries a zero CI in either fleet.

---

## 2. Credit-fraction distributions under the two v2 crediting modes

Definitions audited (plan §1, v2): **`clean_capture`** — eligible zero-carbon fuels
1.0, `gas_cc_ccs` at `federal_ces_ccs_capture_fraction` (0.90), unabated fossil 0.
**`cesa_ci`** — eligible fuels `clip(1 − CI/0.82, 0, 1)`; extended to unabated
`gas_cc` iff CI ≤ 0.45 t/MWh; other unabated fossil 0. Neither 2026 fleet contains a
`gas_cc_ccs` unit (retrofits gated `ccs_retrofit_available_year = 2028`, new-build
CCS `ccs_available_year = 2030`), so today's fleet-level difference between the modes
is entirely (a) the unabated-CC pathway and (b) abated-gas crediting arithmetic once
CCS exists (§3.3). Wind/solar/hydro/geothermal/OSW credit 1.0 identically in both
modes (CI = 0) and sit outside these thermal-fleet tables (wind/solar are zonal
pools, hydro is energy-limited plants added at dispatch).

### 2.1 Capacity-weighted credit fraction by fuel

**ERCOT:**

| fuel | MW | f `clean_capture` | f `cesa_ci` (measured CI) | f `cesa_ci` (physical-HR default CI) |
|---|---:|---:|---:|---:|
| nuclear | 4,980 | 1.0 | 1.0 | 1.0 |
| gas_cc | 37,241 | 0.0 | 0.412 | 0.4 |
| coal | 13,964 | 0.0 | 0.0 | 0.0 |
| gas_st | 11,296 | 0.0 | 0.0 | 0.0 |
| gas_ct | 10,971 | 0.0 | 0.0 | 0.0 |

**PJM:**

| fuel | MW | f `clean_capture` | f `cesa_ci` (measured CI) | f `cesa_ci` (physical-HR default CI) |
|---|---:|---:|---:|---:|
| nuclear | 33,492 | 1.0 | 1.0 | 1.0 |
| gas_cc | 59,719 | 0.0 | 0.472 | 0.465 |
| coal | 35,433 | 0.0 | 0.0 | 0.0 |
| gas_st | 9,490 | 0.0 | 0.0 | 0.0 |
| gas_ct | 26,392 | 0.0 | 0.0 | 0.0 |
| oil | 4,424 | 0.0 | 0.0 | 0.0 |
| biomass | 1,745 | 0.0 | 0.0 | 0.0 |

Thermal-fleet capacity-weighted totals: ERCOT `clean_capture` 0.063 vs `cesa_ci`
0.259; PJM 0.196 vs 0.361. The `cesa_ci` uplift is entirely the unabated-CC pathway:
it hands ~0.41-0.47 average crediting to the CC fleet, i.e. **under `cesa_ci` a
premium P pays the average eligible CCGT ≈ 0.52-0.54 × P per MWh** (credited-set
capacity-weighted f: ERCOT 0.518, PJM 0.540), while under `clean_capture` the same
fleet earns zero until it retrofits. An efficient CCGT at CI ≈ 0.37 earns f ≈ 0.55 —
matching the plan §1 statement.

### 2.2 The 0.45 line — who clears it

**ERCOT gas-CC:**

- 60 plants, 37,241 MW; capacity-weighted CI **0.4353** t/MWh on measured rates vs **0.4392** on the physical-HR-default counterfactual.
- Clears 0.45 with measured rates: **43 of 60 plants, 29,659 MW (79.6%)**; with physical-HR defaults: 43 plants, 28,697 MW (77.1%).
- Measured rates flip **1,670 MW into** the credited set and **708 MW out** of it.
- Capacity-weighted f of the credited (eligible) set: **0.518**.
- v2-uncovered gas_cc: 14 plants, 4,070 MW (CI = physical-HR default at the LP boundary).

**PJM gas-CC:**

- 84 plants, 59,719 MW; capacity-weighted CI **0.3987** t/MWh on measured rates vs **0.4104** on the physical-HR-default counterfactual.
- Clears 0.45 with measured rates: **65 of 84 plants, 52,270 MW (87.5%)**; with physical-HR defaults: 70 plants, 54,090 MW (90.6%).
- Measured rates flip **1,647 MW into** the credited set and **3,467 MW out** of it.
- Capacity-weighted f of the credited (eligible) set: **0.54**.
- v2-uncovered gas_cc: 7 plants, 168 MW (CI = physical-HR default at the LP boundary).

Full plant-level tables (every CC plant, sorted by CI) are in Appendix A; the
announced (EIA-860 planned, construction-committed) CCGTs:

**ERCOT announced:**

| plant | name | MW | online | HR (MMBtu/MWh) | CI HR-default | CI at LP (after v2) | CEMS data | clears 0.45 | f |
|---:|---|---:|---:|---:|---:|---:|:-:|:-:|---:|
| 68606 | Cedar Bayou 5 | 674 | 2028 | 6.3 | 0.359 | 0.36 | — | Y | 0.561 |
| 69566 | CPV Basin Ranch Energy Center | 672 | 2029 | 6.3 | 0.359 | 0.36 | — | Y | 0.561 |
| 69566 | CPV Basin Ranch Energy Center | 672 | 2029 | 6.3 | 0.359 | 0.36 | — | Y | 0.561 |

**PJM announced:**

| plant | name | MW | online | HR (MMBtu/MWh) | CI HR-default | CI at LP (after v2) | CEMS data | clears 0.45 | f |
|---:|---|---:|---:|---:|---:|---:|:-:|:-:|---:|
| 66918 | Trumbull Energy Center | 276 | 2026 | 6.3 | 0.359 | 0.369 | Y | Y | 0.55 |
| 66918 | Trumbull Energy Center | 276 | 2026 | 6.3 | 0.359 | 0.369 | Y | Y | 0.55 |
| 66918 | Trumbull Energy Center | 349 | 2026 | 6.3 | 0.359 | 0.369 | Y | Y | 0.55 |

All announced CCGTs enter at the h-class default HR (6.30 MMBtu/MWh → CI 0.359) and
clear the line at f ≈ 0.55-0.56. Trumbull (PJM, online 2026) already has CEMS
commissioning history, so the v2 override books its measured 0.369 the moment
`build_dispatch_fleet` runs — evidence the entrant→measured handoff works with no new
machinery. Note `load_planned_additions` carries **thermal** units only
(fleet.py:6441-6462); announced wind/solar/storage ride the zonal pools/storage
screens and simply credit 1.0 (or per `federal_ces_storage_eligible`) when built.

### 2.3 Sensitivity of the credited set to measured-vs-fallback rates

Counterfactual: the same fleet built with `use_plant_emission_rates_v2=False`, so
every unit carries the true production fallback — `get_emission_rate(fuel, base_hr)`
on the plant's **physical** heat rate (fleet.py:9708-9727; per the R2/EM-4 comment
the bid-tranche HR with its offer-curve multipliers is deliberately NOT used for
CO2). Fleet averages barely move (capacity-weighted CC fraction: ERCOT 0.412 vs
0.400, PJM 0.472 vs 0.465; capw CI 0.435 vs 0.439 / 0.399 vs 0.410) — the physical-HR
default is a decent *average* prior. The 0.45 **boundary** is where it fails.
Plant-level flips:

**ERCOT** — 2 plants / 1.7 GW flip *into* eligibility on measured rates, 2 plants /
0.7 GW flip *out*:

| plant | name | MW | CI measured | CI HR-default | direction |
|---:|---|---:|---:|---:|---|
| 4939 | Barney M Davis | 730 | 0.426 | 0.456 | measured→eligible |
| 55132 | Tenaska Gateway Generating Stati | 940 | 0.419 | 0.478 | measured→eligible |
| 55206 | Corpus Christi Energy Center | 237 | 0.507 | 0.32 | measured→ineligible |
| 55464 | Deer Park Energy Center | 470 | 0.53 | 0.339 | measured→ineligible |

**PJM** — 3 plants / 1.6 GW in, 8 plants / 3.5 GW out (net: the credited set
*shrinks* from 90.6% to 87.5% of CC MW on measured rates):

| plant | name | MW | CI measured | CI HR-default | direction |
|---:|---|---:|---:|---:|---|
| 3176 | Hunlock Power Station | 125 | 0.43 | 0.459 | measured→eligible |
| 3797 | Chesterfield | 386 | 0.416 | 0.477 | measured→eligible |
| 10030 | Energy Center Dover | 59 | 0.515 | 0.398 | measured→ineligible |
| 10633 | Hopewell Cogeneration | 378 | 0.645 | 0.439 | measured→ineligible |
| 10805 | Kenilworth Energy Facility | 24 | 0.658 | 0.404 | measured→ineligible |
| 55216 | Morris Cogeneration LLC | 194 | 0.729 | 0.361 | measured→ineligible |
| 55337 | Ironwood LLC | 760 | 0.606 | 0.418 | measured→ineligible |
| 55690 | Bethlehem Power Plant | 1,136 | 0.437 | 0.465 | measured→eligible |
| 55701 | Fremont Energy Center | 685 | 0.507 | 0.4 | measured→ineligible |
| 55710 | Allegheny Energy Units 3 4 & 5 | 556 | 0.528 | 0.359 | measured→ineligible |
| 55976 | Hunterstown Power Plant | 810 | 0.607 | 0.408 | measured→ineligible |

The out-flips are the systematic pattern: CHP/cogen and heavily duct-fired units book
*all* stack CO2 over net **electric** MWh, so their measured CI is far worse than the
electric-HR default implies (Morris 0.361→0.729, Kenilworth 0.404→0.658, Hopewell
0.439→0.645, Hunterstown 0.408→0.607, Ironwood 0.418→0.606, Deer Park 0.339→0.530) —
the measured rate correctly refuses ~4.2 GW credit that the fallback would grant.
The in-flips are boundary-straddlers (0.45-0.48 default, 0.42-0.44 measured). Two
conclusions: **run `cesa_ci` on the v2 measured rates** (already the fleet default),
and treat the CEMS-**uncovered** CC capacity with suspicion — ERCOT's 4.1 GW /
PJM's 0.2 GW uncovered plants are mostly industrial cogens whose only available CI is
the flattering HR default (0.29-0.36), exactly the class the measured pattern shows
to be optimistic by 0.2-0.4 t/MWh. Flagged as owner item O-3.

### 2.4 Class-median entrant/uncovered fallback (illustrative)

If the owner wants the estimator's class-median fallback (plan §2.1 step 4) wired for
credited-but-uncovered units, these are the values it would hand out today
(gen-weighted median over each ISO's full 2018-2025 plant-year history;
`plant_group` from the master plant registry — ERCOT-only, so PJM pools to OTHER):

**ERCOT:**

| class (plant_group / fuel) | gen-wt median CI (t/MWh) | implied cesa_ci f (if gas_cc) |
|---|---:|---:|
| CC_CHP / gas | 0.4084 | 0.502 |
| CC_REGULAR / gas | 0.3957 | 0.517 |
| COAL / coal | 1.0654 | 0.000 |
| COAL / gas | 0.9103 | 0.000 |
| CT_CHP / gas | 0.7641 | 0.068 |
| CT_PEAKER / gas | 0.6067 | 0.260 |
| OTHER / biomass | 1.3892 | 0.000 |
| OTHER / coal | 1.0177 | 0.000 |
| OTHER / gas | 0.4781 | 0.417 |

**PJM:**

| class (plant_group / fuel) | gen-wt median CI (t/MWh) | implied cesa_ci f (if gas_cc) |
|---|---:|---:|
| OTHER / biomass | 1.237 | 0.000 |
| OTHER / coal | 0.9598 | 0.000 |
| OTHER / gas | 0.3809 | 0.535 |
| OTHER / oil | 0.9706 | 0.000 |

The ERCOT CC_REGULAR median (0.396 → f = 0.517) is a far better prior for an
uncovered merchant CC than its own registry-HR default, and it would *deny* the
0.29-0.33 cogen CIs that the HR default currently produces. PJM's pooled 0.381 is
CC-dominated (CCs are ~84% of measured PJM gas energy) but technically mixes classes;
a PJM-grouped registry would be needed to do this properly (§6 O-3).

### 2.5 The 0.45 interpretation flag (restated from plan §1)

All numbers above read 0.45 as an **eligibility cutoff** with f still computed
against 0.82 (the plan's stated interpretation, pending the owner micro-check). If
the intent were instead `f = 1 − CI/0.45`, the efficient 0.37-CI CCGT drops from
f ≈ 0.55 to f ≈ 0.18 and the credited-set capacity-weighted f falls from ≈0.52-0.54
to ≈0.10-0.12 — a ~5× change in what a given premium pays unabated gas. The two
readings are NOT interchangeable; W2-A must not start before this is resolved
(§6 O-1).

---

## 3. Reconciling the three capture-rate knobs (plan §11 item 4)

### 3.1 Inventory

| knob | value | where | citation | role | consumers |
|---|---:|---|---|---|---|
| `ccs_capture_rate` | 0.90 | `scenarios.py:411`, Tier 2 | **none** ("fraction of CO2 captured by CCUS"; parameters.json flags `needs-citation`) | engineering, new-build | `capacity.py:1734-1735` (LCOE screen: `captured`/`residual` split; 45Q offset on captured tonnes at `:1742`), `capacity.py:2027-2037` (`_make_new_generator`: `emission_rate_co2 = 0.36 × (1−rate)` = **0.036 t/MWh**; transport cost folded into VOM) |
| `ccs_retrofit_capture_rate` | 0.90 | `scenarios.py:430-431`, Tier 2 | "Source: NETL design basis for amine scrubbing" (comment; the parameters.json harvester dropped this line — code comment is authoritative) | engineering, retrofit | `capacity.py:2924` (screen: `carbon_avoided`), `:2969-2971` (conversion: `emission_rate_co2 ×= (1−rate)` on the host's own measured rate → residual ≈ 0.040-0.044 t/MWh at the ISOs' measured CC fleet averages; `fuel_type → "gas_cc_ccs"` at `:2972`) |
| `CCUS_PARAMS["gas_cc_ccs_90"]["capture_rate"]` | 0.90 | `constants.py:4203`, Tier 2 | "NETL 2022 Case B31B" — the only capture knob with a real citation | **dead code** | none — capacity.py reads B31B's HR penalty (1.16), VOM adder, capex etc. from `CCUS_PARAMS` but the capture fraction always comes from `config.ccs_capture_rate` |
| `federal_ces_ccs_capture_fraction` (proposed) | 0.90 (0.95 sens.) | plan §5.1 (not yet in code) | owner simplification ("assume 90 or 95% capture") | **policy crediting**, `clean_capture` mode only | W1-A resolver |

Related but distinct: `co2_transport_storage_cost` = 15 $/t (scenarios.py:412,
new-build only); `ccs_retrofit_hr_penalty` = 0.12 (NETL Rev 4); 45Q pays
`$85/t × captured` (`policy/ira.py:13,55-75`), consumed **only** by the new-build
LCOE — the retrofit screen has neither 45Q nor transport cost (the §11 defect list).
Petra Nova (the one real CCS plant, backcast special-case, fleet.py:9073-9107)
carries **no capture reduction at all** — its CI is the generic CT_CHP HR-derived
rate. Emissions accounting (`results/emissions.py`) has no capture logic: captured
tonnage exists only inside screen economics; results see only residual rates.

### 3.2 How the three relate

The two live engineering knobs set **physics**: the unit's residual
`emission_rate_co2` at build/retrofit time, hence its dispatch cost under a carbon
price, its reported emissions, and — decisive here — **the CI that `cesa_ci` would
read**. The proposed policy field sets **crediting** in `clean_capture` mode only.
The three coincide numerically at 0.90 today, but they are not coupled:

- **`clean_capture` @ 0.90:** abated gas credits f = 0.90. Consistent with the
  engineering fields by numerical accident.
- **`clean_capture` @ 0.95 (sensitivity):** credits f = 0.95 while the engineering
  knobs still produce a 0.036-0.044 t/MWh residual — i.e. the certificate asserts 5
  points more abatement than the modeled plant delivers. Defensible as a pure policy
  assumption (certificates ≠ physics) but must be documented as such, and the
  sensitivity is **only** meaningful in this mode.
- **`cesa_ci`:** the capture fraction is **inert** — crediting reads the unit's
  residual CI directly: new-build f = 1 − 0.036/0.82 = **0.956**; retrofit at the
  measured fleet-average host CI: ERCOT 1 − 0.0435/0.82 = **0.947**, PJM
  1 − 0.0399/0.82 = **0.951** (plan §1's "≈0.955 at 90% capture" confirmed). Note
  `cesa_ci` therefore credits abated gas *more* than `clean_capture` (≈0.95 vs 0.90)
  — a deliberate structural difference between the modes worth one sentence in the
  campaign report.

### 3.3 Recommendations (for W1-A registration + W2-C)

1. Register `federal_ces_ccs_capture_fraction` with the source string "owner
   simplification (plan §10 item 1); numerically anchored to NETL Cost & Performance
   Baseline Rev 4 (2022) Case B31B 90% amine capture — same basis as
   `ccs_capture_rate`/`ccs_retrofit_capture_rate`" and a note that it is
   crediting-only (`clean_capture`), inert under `cesa_ci`.
2. Fix `ccs_capture_rate`'s missing citation while touching this area (NETL 2022 Case
   B31B — the citation already sits on the dead `CCUS_PARAMS` key one file over), and
   have W2-C either consume or delete the dead `CCUS_PARAMS…capture_rate` key
   (rule 26 spirit: a dead parameter that still parses invites divergence — the
   `_90`-suffixed tech key silently contradicts any swept `ccs_capture_rate ≠ 0.90`,
   because B31B's 1.16 HR penalty is capture-rate-dependent physically).
3. Add a `__post_init__` consistency warning (not an error) when
   `federal_ces_enabled and federal_ces_crediting == "clean_capture" and
   federal_ces_ccs_capture_fraction != ccs_capture_rate` — the 0.95 sensitivity then
   states its physics divergence explicitly in the run log.
4. W2-C note: `ira_ccus_45q_last_year = 2032` models 45Q as "phasing out post-2032";
   the statute is a **begin-construction deadline (before 2033)** plus a **12-year
   credit window from placed-in-service** (§4 below) — roughly right for gating NEW
   projects, wrong for truncating the credit stream of a 2030 build at 2032. Already
   §11's item 1 (credit-window-aware annualization); the OBBBA finding in §4
   (45Q preserved/expanded, unlike PTC/ITC) removes any reason to sunset it early.

---

## 4. Citation packet (final) + parameters.json drafts

Primary texts verified from govinfo.gov (GPO official mirrors; congress.gov and
federalregister.gov 403 this environment's fetcher — the canonical URLs below are
listed alongside the verified govinfo copies).

### 4.1 The 0.82 t/MWh benchmark — Bingaman S.2146 (112th Congress, 2012)

- **Cite:** S. 2146, 112th Cong., 2d Sess. — "Clean Energy Standard Act of 2012"
  (Sen. Bingaman, introduced 2012-03-01), §2 adding PURPA §610.
- **Benchmark:** new §610(b)(1)(B)(ii) — clean energy includes "a source of energy,
  other than biomass, with lower annual carbon intensity than **0.82 metric tons of
  carbon dioxide equivalent per megawatt-hour**".
- **Crediting formula:** §610(f)(1) — credits/MWh = 1.0 − (annual carbon intensity in
  metric tons per MWh ÷ **0.82**); negative credits prohibited (§610(f)(2)); CI is
  **net** annual CO2e emissions ÷ annual generation (§610(g)(1)).
- **Secondary:** CRS R42522 (2012-05-09) reproduces the formula and worked example
  (CI 0.41 → 0.5 credit) and flags that the bill does not state a gross-vs-net
  *output* basis; EIA, *Analysis of the Clean Energy Standard Act of 2012* (May 2012,
  requested by Sen. Bingaman) — the model-analysis precedent for this feature.
- **URLs:** congress.gov/bill/112th-congress/senate-bill/2146; verified text
  govinfo.gov/content/pkg/BILLS-112s2146is; CRS R42522; EIA
  eia.gov/analysis/requests/bces12/pdf/cesbing.pdf.

### 4.2 The partial-crediting design precedent — CESA S.1359 (116th Congress, 2019)

- **Cite:** S. 1359, 116th Cong., 1st Sess. — "Clean Energy Standard Act of 2019"
  (Sen. Smith, introduced 2019-05-08; House companion H.R. 2597), §2 adding PURPA
  §610.
- **Same construction, different benchmark:** §610(f)(1) credits/MWh =
  1 − CI/benchmark, but §610(b)(1) sets the "applicable carbon intensity" at
  **0.4 metric tons CO2e/MWh** — 2× stricter than S.2146. Credits cap at 1/MWh
  (§610(f)(9)); a temporary 1.5× innovation multiplier exists for dispatchable
  low-carbon tech (§610(f)(10)); CI includes an upstream **methane-leakage
  adjustment** for natural gas (§610(g)(2), EPA MARKAL leakage rates).
- **Model mapping:** our `federal_ces_ci_benchmark_t_per_mwh = 0.82` is the
  **S.2146** number; S.1359 is cited for the fractional-crediting design and as the
  source of a candidate stricter-benchmark sensitivity (0.4). Model CI is stack CO2
  per net MWh — no CO2e/CH4 uplift; both bills use CO2e. At ERCOT/PJM CC CIs the
  CO2-vs-CO2e gap from combustion non-CO2 GHGs is negligible; an S.1359-style
  upstream-leakage adder would NOT be (flag if the 0.4 sensitivity is ever run).
- **URLs:** congress.gov/bill/116th-congress/senate-bill/1359; verified text
  govinfo.gov/content/pkg/BILLS-116s1359is.

### 4.3 The 0.45 t/MWh line — EPA §111(b) new-CCGT NSPS correspondence

- **Primary anchor (2015 rule):** 80 FR 64510 (2015-10-23), 40 CFR part 60 subpart
  TTTT: newly constructed/reconstructed **base-load** natural-gas combined cycle —
  **1,000 lb CO2/MWh-gross** (12-op-month rolling average), with the equivalent
  optional net-output standard **1,030 lb CO2/MWh-net** (rule's own 3%
  auxiliary-load equivalence).
- **Conversion:** 1,000 lb/MWh = 453.6 kg/MWh = **0.4536 t/MWh**; the model's
  0.45 t/MWh-net = 992 lb/MWh — within 0.8% of the gross standard and **~3.6%
  stricter** than the rule's net-basis equivalent (0.467 t/MWh-net). Since model CI
  is net-MWh-based, the honest one-liner is: *0.45 t/MWh-net ≈ the 2015 §111(b)
  new-CCGT NSPS (1,000 lb CO2/MWh-gross; 1,030 lb ≈ 0.467 t on the rule's net
  basis), rounded slightly strict.*
- **2024 update (status-noted, not the anchor):** 89 FR 39798 (2024-05-09), subpart
  TTTTa — phase 1 for large (>2,000 MMBtu/h) base-load turbines **800 lb
  CO2/MWh-gross** (0.363 t-gross; sliding to 1,250 lb for the smallest), phase 2 from
  2032-01-01 reflecting 90%-capture CCS (100-150 lb/MWh-gross). **Repeal pending:**
  proposed 90 FR 25752 (2025-06-17); final rule sent to OMB 2026-05-14, not yet
  published as of 2026-07-17 (Harvard EELP tracker). Hence the durable citation for
  0.45 is the 2015 line, with the 2024/repeal status recorded in the notes field.
- **URLs:** govinfo.gov/content/pkg/FR-2015-10-23/html/2015-22837.htm;
  govinfo.gov/content/pkg/FR-2024-05-09/html/2024-09233.htm;
  govinfo.gov/content/pkg/FR-2025-06-17/html/2025-10991.htm.

### 4.4 45Q (context for §3/W2-C stacking)

IRC §45Q as amended by IRA 2022 (Pub. L. 117-169 §13104): base $17/t × 5
(prevailing-wage multiplier, §45Q(h)) = **$85/t** geologic storage; **12-year credit
window from placed-in-service** (§45Q(a)(3)-(4)); qualified facilities must begin
construction **before 2033-01-01** (§45Q(d)(1)). **OBBBA 2025 (Pub. L. 119-21
§70522) did NOT phase 45Q out** — it granted EOR/utilization parity ($85/t for
facilities placed in service after 2025-07-04) and added foreign-entity
restrictions; deadline and window unchanged. Unlike the §45Y/§48E phase-outs the
repo already models, 45Q survives — reinforcing §11's "add 45Q to the retrofit
screen" and the §3.3 note on `ira_ccus_45q_last_year`.

### 4.5 parameters.json entry drafts — every plan §5.1 field

Conventions per `docs/parameter-citations.md`: ScenarioConfig fields register as
`scenario.<field>`; entries carry the `frontend/data/parameters.json` field order
(`param_id, display_name, value, unit, domain, tier, source, source_date,
page_or_table, url, notes, old_repo_location, last_verified, flags`);
`scripts/validate_parameters.py` hard-fails CI on any missing entry and warns on
code/registry value drift. All fields below are Tier 1 (plan §5.1), domain "Policy".
Drafts (W1-A pastes these, replacing the auto-generated harvester output):

```json
[
  {
    "param_id": "scenario.federal_ces_enabled",
    "display_name": "Federal CES Enabled",
    "value": false, "unit": "", "domain": "Policy", "tier": 1,
    "source": "Model design decision — national CES EAC-premium feature gate; forecast-only (backcast guard raises), default-off => byte-identical dispatch when disabled",
    "source_date": "2026-07",
    "page_or_table": "national-ces-eac-premium-plan-2026-07.md §5.1",
    "url": "",
    "notes": "Owner decision register 2026-07-17 (plan §10).",
    "old_repo_location": "", "last_verified": "2026-07-17", "flags": ["modeled"]
  },
  {
    "param_id": "scenario.federal_ces_premium_usd_per_mwh",
    "display_name": "Federal CES Premium ($/MWh)",
    "value": 0.0, "unit": "real 2026$/MWh", "domain": "Policy", "tier": 1,
    "source": "Owner scenario input; first-run ladder {10, 20, 30} real 2026$/MWh (plan D8). Plausibility: EAC_PRICE_REFERENCE $2-40/MWh by tech (constants.py:4786-4801); scope2-lce-portfolio ADR 0021 breakevens $3-20/MWh (illustrative)",
    "source_date": "2026-07",
    "page_or_table": "plan §10 item 3; ces-ci-crediting-audit-2026-07.md §5",
    "url": "",
    "notes": "Real-dollar convention: constant real premium = CPI-tracking nominal (REAL_DOLLAR_BASE_YEAR).",
    "old_repo_location": "", "last_verified": "2026-07-17", "flags": ["modeled"]
  },
  {
    "param_id": "scenario.federal_ces_premium_escalation_real",
    "display_name": "Federal CES Premium Escalation (real)",
    "value": 0.0, "unit": "fraction/yr", "domain": "Policy", "tier": 1,
    "source": "Owner decision D3/D8 (2026-07-17): escalation 0%/yr real confirmed (= CPI-tracking nominal); field retained for real-growth sensitivities",
    "source_date": "2026-07", "page_or_table": "plan §4 D3", "url": "",
    "notes": "", "old_repo_location": "", "last_verified": "2026-07-17",
    "flags": ["modeled"]
  },
  {
    "param_id": "scenario.federal_ces_premium_by_year",
    "display_name": "Federal CES Premium By Year",
    "value": null, "unit": "{year: real 2026$/MWh}", "domain": "Policy", "tier": 1,
    "source": "Model design decision — sparse knots, linear interpolation, edge-held; overrides base+escalation. Pattern precedent: STATE_RPS_FLOORS (rps.py:8-39)",
    "source_date": "2026-07", "page_or_table": "plan §5.1", "url": "",
    "notes": "YAML round-trip coerces str keys to int.",
    "old_repo_location": "", "last_verified": "2026-07-17", "flags": ["modeled"]
  },
  {
    "param_id": "scenario.federal_ces_crediting",
    "display_name": "Federal CES Crediting Mode",
    "value": "clean_capture", "unit": "", "domain": "Policy", "tier": 1,
    "source": "Owner decision D1 (2026-07-17): two modes — clean_capture (default; clean 1.0, abated gas at assumed capture fraction, unabated 0) and cesa_ci (S.2146-style fractional crediting)",
    "source_date": "2026-07", "page_or_table": "plan §1, §4 D1", "url": "",
    "notes": "Validated in __post_init__ against the two mode names.",
    "old_repo_location": "", "last_verified": "2026-07-17", "flags": ["modeled"]
  },
  {
    "param_id": "scenario.federal_ces_ccs_capture_fraction",
    "display_name": "Federal CES CCS Capture Fraction",
    "value": 0.9, "unit": "fraction", "domain": "Policy", "tier": 1,
    "source": "Owner simplification (plan §10 item 1: 'assume 90 or 95% capture'; 0.95 = sensitivity). Numerically anchored to NETL Cost & Performance Baseline Rev 4 (2022) Case B31B 90% amine capture — same engineering basis as scenario.ccs_capture_rate / scenario.ccs_retrofit_capture_rate",
    "source_date": "2022",
    "page_or_table": "NETL Rev 4 Case B31B; ces-ci-crediting-audit-2026-07.md §3",
    "url": "",
    "notes": "Crediting-only: consumed by clean_capture mode; INERT under cesa_ci (that mode reads the unit's residual CI, giving f≈0.947-0.956 at 90% engineering capture). At 0.95 the certificate credits more abatement than the engineering capture fields produce — policy assumption, documented divergence.",
    "old_repo_location": "", "last_verified": "2026-07-17", "flags": ["modeled"]
  },
  {
    "param_id": "scenario.federal_ces_ci_benchmark_t_per_mwh",
    "display_name": "Federal CES CI Benchmark (t/MWh)",
    "value": 0.82, "unit": "tCO2e/MWh", "domain": "Policy", "tier": 1,
    "source": "Clean Energy Standard Act of 2012, S. 2146 (112th Cong., Bingaman), new PURPA §610(b)(1)(B)(ii) and §610(f)(1): credits/MWh = 1 − CI/0.82 (metric tons CO2e/MWh); negative credits prohibited. Secondary: CRS R42522; EIA, Analysis of the Clean Energy Standard Act of 2012 (May 2012)",
    "source_date": "2012-03-01",
    "page_or_table": "S.2146 §610(b)(1)(B)(ii), §610(f)(1)",
    "url": "https://www.congress.gov/bill/112th-congress/senate-bill/2146",
    "notes": "NOT S.1359: the 2019 Smith bill (S.1359, 116th) uses the same 1 − CI/benchmark construction with a 0.4 tCO2e/MWh benchmark (§610(b)(1)) — candidate stricter sensitivity, not the default. Model CI is stack CO2 per net MWh (no CO2e/upstream-CH4 uplift; both bills use CO2e).",
    "old_repo_location": "", "last_verified": "2026-07-17", "flags": []
  },
  {
    "param_id": "scenario.federal_ces_unabated_ci_threshold_t_per_mwh",
    "display_name": "Federal CES Unabated-CC CI Threshold (t/MWh)",
    "value": 0.45, "unit": "tCO2/MWh net", "domain": "Policy", "tier": 1,
    "source": "Owner-set eligibility line (450 kg/MWh), ≈ EPA CAA §111(b) NSPS for new base-load NGCC, 80 FR 64510 (2015-10-23), 40 CFR 60 subpart TTTT: 1,000 lb CO2/MWh-gross (= 0.4536 t/MWh; optional net-basis equivalent 1,030 lb = 0.467 t/MWh-net). 0.45 t/MWh-net = 992 lb/MWh — the NSPS line rounded slightly strict",
    "source_date": "2015-10-23",
    "page_or_table": "80 FR 64510, Table 15 (80 FR 64602)",
    "url": "https://www.govinfo.gov/content/pkg/FR-2015-10-23/html/2015-22837.htm",
    "notes": "Gross-vs-net caveat: model CI is net-MWh-based; the NSPS primary standard is gross. Status: the 2024 update (89 FR 39798, subpart TTTTa; phase-1 800 lb/MWh-gross large units, phase-2 CCS-based 100-150 lb from 2032) is under proposed repeal (90 FR 25752; final at OMB 2026-05); the 2015 line is the durable anchor. cesa_ci-only; interpretation = eligibility cutoff, f still computed vs 0.82 (owner micro-check pending, plan §10 item 1).",
    "old_repo_location": "", "last_verified": "2026-07-17", "flags": []
  },
  {
    "param_id": "scenario.federal_ces_eligible_fuels",
    "display_name": "Federal CES Eligible Fuels",
    "value": ["nuclear", "wind", "solar", "hydro", "geothermal", "offshore_wind", "gas_cc_ccs", "hydrogen_ct", "hydrogen_ccgt"],
    "unit": "", "domain": "Policy", "tier": 1,
    "source": "Owner decision (plan §1 Eligibility, 2026-07-17): all zero-carbon + abated gas + hydrogen turbines; existing units credit identically to new (no vintage gate). Excluded: unabated fossil (cesa_ci variant is the unabated-CC pathway), storage discharge, biomass",
    "source_date": "2026-07", "page_or_table": "plan §1", "url": "",
    "notes": "", "old_repo_location": "", "last_verified": "2026-07-17",
    "flags": ["modeled"]
  },
  {
    "param_id": "scenario.federal_ces_storage_eligible",
    "display_name": "Federal CES Storage Eligible",
    "value": false, "unit": "", "domain": "Policy", "tier": 1,
    "source": "Owner decision D5 (2026-07-17): storage discharge creates no new attribute; storage adapts endogenously via arbitrage. Toggle retained for sensitivity",
    "source_date": "2026-07", "page_or_table": "plan §4 D5", "url": "",
    "notes": "", "old_repo_location": "", "last_verified": "2026-07-17",
    "flags": ["modeled"]
  },
  {
    "param_id": "scenario.federal_ces_replaces_state_rps",
    "display_name": "Federal CES Replaces State RPS",
    "value": false, "unit": "", "domain": "Policy", "tier": 1,
    "source": "Model design decision — pure-federal counterfactual switch; suppresses state RPS rows in RPS ISOs (CAISO/NYISO/NEISO). Moot for ERCOT/PJM (no RPS row: STATE_RPS_FLOORS ERCOT all-0.0, PJM absent)",
    "source_date": "2026-07", "page_or_table": "plan §1 policy interaction", "url": "",
    "notes": "", "old_repo_location": "", "last_verified": "2026-07-17",
    "flags": ["modeled"]
  }
]
```

(Validator behavior to expect: `validate_parameters.py` builds the expected id set
from ScenarioConfig fields, so all ten entries above become REQUIRED the moment W1-A
adds the fields — landing these drafts in the same PR keeps CI green. The
auto-harvester would otherwise register them `needs-citation` from the inline
comments; these drafts replace that.)

---

## 5. Ladder {10, 20, 30} sanity check

### 5.1 vs `EAC_PRICE_REFERENCE` (constants.py:4786-4801; documentation-only ranges)

| tech | low | mid | high | source comment |
|---|---:|---:|---:|---|
| eac_nuclear_zec | 10 | 17 | 25 | NY PSC Order, Case 15-E-0302; IL FEJA |
| eac_wind | 2 | 8 | 15 | PJM GATS, S&P Global Platts |
| eac_solar | 2 | 10 | 20 | PJM GATS, S&P Global Platts |
| eac_offshore_wind | 20 | 30 | 40 | NJ BPU OREC orders, NYSERDA |
| eac_geothermal | 5 | 10 | 15 | CA CES program, analogy to nuclear ZEC |
| eac_gas_cc_ccs | 10 | 15 | 25 | 45Q market + state CES analogy |
| eac_storage | 0 | 5 | 10 | limited precedent, modeling assumption |

- **$10** = the ZEC low / CCS low, at-or-above wind (8) and solar (10) mids.
- **$20** ≥ every mid except offshore wind (30); inside nuclear-ZEC/CCS high bands.
- **$30** > every high except offshore wind (40). For abated gas, premium ×
  credit-fraction lands 30 × 0.956 ≈ $28.7 under `cesa_ci` — just above the CCS
  reference high (25); 20 × 0.956 ≈ $19.1 sits inside it.

### 5.2 vs scope2-lce-portfolio prior art (standalone; NOT importable code)

`scope2-lce-portfolio/data/eac/eac_prices.csv` (28 rows; years 2030/2040/2050;
forward-filled annual series per its ADR 0020) spans **$3-20/MWh**: existing-fleet
attributes $3-6 flat (nuclear 4, hydro 3 — anchored to Platts Type-2 hourly
certificates $0.90-5.00/MWh and national voluntary RECs $2-7/MWh, deliberately NOT
to ZECs), new-build attribute premia $5-20 (2030) declining to $3-16 (2050); max =
gas_cc_ccs_new 2030 at $20. ADR 0021 (`docs/decisions/0021-breakeven-eac-derivation.md`)
derives breakevens as the residual $/MWh clearing a 9%/20-yr hurdle after LMP + 45Q +
capacity revenue, and labels every shipped value **illustrative** pending per-ISO
regeneration; formula-faithful worked examples put new-build CCS at ~$17.5 (ERCOT) /
~$4.8 (PJM, $100/kW-yr capacity offset), onshore wind ~$8-18, solar ~$20-30, offshore
wind ~$89. (The CSV declares no dollar-year; its ATB-2022$ anchoring puts ≤8%
inflation-basis ambiguity against real 2026$ — immaterial to any conclusion.)

**Read:** the ladder sits in the upper half of and above the observed/derived range —
by design, since a CES premium is a compliance-value analogue, not a voluntary-market
price. $10 stress-tests existing-fleet-only crediting (2-3× voluntary certificates,
at the bottom of policy-instrument territory); $20 reaches the illustrative
new-build/CCS breakeven frontier (= the CSV max, ≈ ERCOT worked CCS breakeven); $30
is deliberately supra-breakeven for everything except offshore wind — the saturation
rung. No change recommended. If a W5 extension ever needs an "observed-market" rung,
add $5, don't move the existing three.

### 5.3 One cross-instrument sanity number

45Q at $85/t equals ≈ $33.9/MWh for a 95%-capture CC (captured-tonnes basis) — the
same order as the $30 rung × 0.9-0.956 crediting. So at the top rung, a CES
certificate is worth roughly one 45Q to an abated-gas unit; they stack as separate
instruments (plan D2/§11 Q1). Nothing about the ladder is out of scale with the one
real federal instrument already priced in the model.

---

## 6. Open items handed to the owner / later waves

- **O-1 (blocks W2-A dispatch wiring of `cesa_ci`):** the 0.45 interpretation
  micro-check (cutoff vs denominator) — §2.5 quantifies the 5× stakes. Plan §10
  item 1 already flags it; this audit's numbers assume the cutoff reading.
- **O-2 (W1-A, mechanical):** re-anchor the 0.82 citation to S.2146 §610(f)(1)
  everywhere the plan/comments say S.1359 (plan §1, §5.1 field comment, §9 rule-5
  row); cite S.1359 for the design + the 0.4 benchmark sensitivity. Use the §4.5
  drafts for parameters.json.
- **O-3 (owner call, W2-A-sized):** uncovered-unit CI under `cesa_ci`. Today 4.1 GW
  of ERCOT CC (industrial cogens) would be credited off HR-default CIs of 0.29-0.36
  that the measured-cogen pattern (§2.3 (ii)) suggests are optimistic. Options: (a)
  accept (they are ~5% of CC energy); (b) wire the estimator's class-median fallback
  (§2.4) for credited-but-uncovered units — needs a PJM plant-group registry to do
  properly; (c) exclude CEMS-uncovered units from `cesa_ci` crediting. Recommend (b)
  long-term, (a) for the first campaign with the caveat in the report.
- **O-4 (W2-C):** the three §3.3 items — cite `ccs_capture_rate`, retire or consume
  the dead `CCUS_PARAMS` capture key, add the crediting-vs-engineering consistency
  warning; plus the `ira_ccus_45q_last_year` window-vs-deadline fix (§4.4).
- **O-5 (campaign reporting):** state in the W4 report that `cesa_ci` credits abated
  gas ≈0.95 vs `clean_capture`'s 0.90 (§3.2) and that ERCOT/PJM CC fleets earn ≈0.52
  / 0.54 × premium per credited MWh (§2.1) — the two modes are NOT nested; neither
  dominates the other for gas.

## 7. Method notes & caveats

- Fleets: production builders at `e1fcb02`, `ScenarioConfig` defaults (the
  keeper-calibrated BAU), year 2026, forecast mode. ERCOT: 633 units / 78.5 GW after
  477 MW confirmed exits (the clean `confirmed-retirements` partition had to be
  regenerated in-session via `scripts/data/curate_confirmed_retirements.py` — it is
  derived/gitignored and absent in a fresh container; W1-B should expect the same).
  PJM: 1,858 units / 170.7 GW (its 8 confirmed exits are all post-2026).
- Energy shares: measured trailing net-MWh for covered plants; class-CF × pmax
  estimate for uncovered (§1.4) — audit-only construction.
- Credit fractions are fleet-input properties (no dispatch): capacity-weighted, and
  "energy" weighting would shift `cesa_ci` CC averages up slightly (efficient units
  run more). The W4 campaign measures the real credited-MWh distribution.
- The plant tables in Appendix A aggregate LP tranche units to plants
  (capacity-weighted CI; tranches of a plant share one measured rate by
  construction).
- Announced-CCGT list = `load_planned_additions` (EIA-860 construction-committed
  statuses U/V/TS beyond the operable vintage): ERCOT 3 CC units / 2,018 MW +
  27 CT / 1,929 MW; PJM 3 CC units / 901 MW + 1 CT / 2 MW. Duplicate-looking rows
  are real separate units at one plant.
- Everything here is repo state + public statutes; no measured 2026 actuals were
  read (the v2 artifact carries no ERCOT/PJM 2026 rows), no holdout year touched, no
  LP solved — rule-22 clean.

---

## Appendix A — full gas-CC plant tables (2026 fleets, measured LP-boundary CI)

### A.1 ERCOT (60 plants)

| plant | name | MW | CI (t/MWh) | CI HR-default | measured | clears 0.45 | f = clip(1−CI/0.82) |
|---:|---|---:|---:|---:|:-:|:-:|---:|
| 50118 | Hal C Weaver Power Plant | 56 | 0.288 | 0.288 | — | Y | 0.648 |
| 55313 | Ingleside Cogeneration | 207 | 0.308 | 0.308 | — | Y | 0.624 |
| 58151 | Central Utility Plant - Texas A& | 18 | 0.318 | 0.318 | — | Y | 0.612 |
| 56152 | Freeport Energy Center | 104 | 0.321 | 0.321 | — | Y | 0.609 |
| 10554 | Formosa Utility Venture Ltd | 373 | 0.322 | 0.322 | — | Y | 0.607 |
| 50043 | Houston Chemical Complex Battleg | 152 | 0.323 | 0.323 | — | Y | 0.606 |
| 52132 | Power Station 4 | 63 | 0.327 | 0.327 | — | Y | 0.602 |
| 52120 | Freeport Energy | 168 | 0.334 | 0.334 | — | Y | 0.593 |
| 54676 | Oyster Creek Unit VIII | 199 | 0.346 | 0.346 | — | Y | 0.578 |
| 60122 | Colorado Bend II | 1,230 | 0.359 | 0.374 | Y | Y | 0.562 |
| 59812 | Wolf Hollow II | 1,231 | 0.37 | 0.379 | Y | Y | 0.549 |
| 55215 | Odessa-Ector Power Plant | 1,153 | 0.374 | 0.383 | Y | Y | 0.544 |
| 55226 | Freestone Energy Center | 1,036 | 0.375 | 0.387 | Y | Y | 0.543 |
| 55137 | Rio Nogales Power Project | 940 | 0.375 | 0.372 | Y | Y | 0.542 |
| 55299 | Channel Energy Center LLC | 370 | 0.376 | 0.291 | Y | Y | 0.542 |
| 55097 | Lamar Power Project | 1,113 | 0.379 | 0.393 | Y | Y | 0.538 |
| 55320 | Wise County Power LLC | 822 | 0.38 | 0.383 | Y | Y | 0.536 |
| 55187 | Channelview Cogeneration Plant | 367 | 0.385 | 0.327 | Y | Y | 0.531 |
| 55062 | Tenaska Frontier Generation Stat | 940 | 0.388 | 0.408 | Y | Y | 0.527 |
| 55230 | Jack County | 1,280 | 0.393 | 0.401 | Y | Y | 0.52 |
| 58005 | Rayburn Energy Station LLC | 803 | 0.395 | 0.405 | Y | Y | 0.519 |
| 55480 | Forney Energy Center | 1,894 | 0.395 | 0.405 | Y | Y | 0.518 |
| 55047 | Pasadena Cogeneration | 326 | 0.397 | 0.378 | Y | Y | 0.516 |
| 55139 | Wolf Hollow I LP | 788 | 0.397 | 0.405 | Y | Y | 0.515 |
| 55123 | Magic Valley Generating Station | 801 | 0.398 | 0.377 | Y | Y | 0.514 |
| 7512 | Arthur Von Rosenberg | 575 | 0.399 | 0.399 | — | Y | 0.513 |
| 55545 | Hidalgo Energy Center | 551 | 0.399 | 0.399 | — | Y | 0.513 |
| 55168 | Bastrop Energy Center | 619 | 0.406 | 0.396 | Y | Y | 0.505 |
| 52088 | Texas City Power Plant | 180 | 0.406 | 0.331 | Y | Y | 0.505 |
| 55098 | Frontera Energy Center | 529 | 0.407 | 0.392 | Y | Y | 0.503 |
| 55153 | Guadalupe Generating Station | 1,088 | 0.408 | 0.421 | Y | Y | 0.503 |
| 55144 | Hays Energy Project | 989 | 0.409 | 0.416 | Y | Y | 0.501 |
| 55091 | Midlothian Energy Facility | 1,734 | 0.412 | 0.422 | Y | Y | 0.497 |
| 55327 | Baytown Energy Center | 373 | 0.413 | 0.35 | Y | Y | 0.496 |
| 54817 | Johnson County | 283 | 0.415 | 0.422 | Y | Y | 0.493 |
| 55223 | Ennis Power Company LLC | 418 | 0.418 | 0.414 | Y | Y | 0.49 |
| 55132 | Tenaska Gateway Generating Stati | 940 | 0.419 | 0.478 | Y | Y | 0.489 |
| 3443 | Victoria | 377 | 0.423 | 0.443 | Y | Y | 0.484 |
| 3441 | Nueces Bay | 730 | 0.425 | 0.417 | Y | Y | 0.482 |
| 4939 | Barney M Davis | 730 | 0.426 | 0.456 | Y | Y | 0.481 |
| 55172 | Thad Hill Energy Center | 807 | 0.426 | 0.435 | Y | Y | 0.481 |
| 58001 | Temple Power Station | 1,606 | 0.434 | 0.439 | Y | Y | 0.47 |
| 7900 | Sand Hill | 696 | 0.439 | 0.42 | Y | Y | 0.464 |
| 56350 | Colorado Bend Energy Center | 654 | 0.452 | 0.457 | Y | N | (0.449) → 0 |
| 55501 | Kiamichi Energy Facility | 1,370 | 0.463 | 0.463 | — | N | (0.436) → 0 |
| 56233 | EG178 Facility | 154 | 0.468 | 0.468 | — | N | (0.429) → 0 |
| 56349 | Quail Run Energy Center | 550 | 0.47 | 0.486 | Y | N | (0.426) → 0 |
| 55086 | Gregory Power Plant | 470 | 0.48 | 0.666 | Y | N | (0.415) → 0 |
| 50109 | Paris Energy Center | 266 | 0.498 | 0.494 | Y | N | (0.393) → 0 |
| 55206 | Corpus Christi Energy Center | 237 | 0.507 | 0.32 | Y | N | (0.382) → 0 |
| 55464 | Deer Park Energy Center | 470 | 0.53 | 0.339 | Y | N | (0.353) → 0 |
| 56806 | Cedar Bayou 4 | 536 | 0.553 | 0.567 | Y | N | (0.326) → 0 |
| 3631 | Sam Rayburn | 193 | 0.561 | 0.557 | Y | N | (0.316) → 0 |
| 4937 | Thomas C Ferguson | 575 | 0.561 | 0.577 | Y | N | (0.316) → 0 |
| 50815 | Odyssey Energy Altura Cogen, LLC | 257 | 0.585 | 0.597 | Y | N | (0.287) → 0 |
| 55154 | Lost Pines 1 Power Project | 244 | 0.601 | 0.617 | Y | N | (0.266) → 0 |
| 3469 | T H Wharton | 1,190 | 0.694 | 0.74 | Y | N | (0.153) → 0 |
| 52176 | C R Wing Cogen Plant | 92 | 0.709 | 0.706 | Y | N | (0.135) → 0 |
| 50127 | Signal Hill Generating LLC | 80 | 0.878 | 0.878 | — | N | (0.0) → 0 |
| 55470 | Green Power 2 | 244 | 2.061 | 1.981 | Y | N | (0.0) → 0 |

### A.2 PJM (84 plants)

| plant | name | MW | CI (t/MWh) | CI HR-default | measured | clears 0.45 | f = clip(1−CI/0.82) |
|---:|---|---:|---:|---:|:-:|:-:|---:|
| 55460 | Indeck Niles Energy Center | 1,082 | 0.339 | 0.374 | Y | Y | 0.586 |
| 61035 | Birdsboro Power | 485 | 0.342 | 0.363 | Y | Y | 0.583 |
| 61322 | Long Ridge Energy Generation | 485 | 0.343 | 0.362 | Y | Y | 0.582 |
| 62949 | Guernsey Power Station | 1,788 | 0.347 | 0.413 | Y | Y | 0.576 |
| 60589 | CPV Fairview Energy Center | 725 | 0.348 | 0.368 | Y | Y | 0.575 |
| 60356 | South Field Energy | 1,210 | 0.351 | 0.38 | Y | Y | 0.572 |
| 59913 | Greensville County Power Station | 1,605 | 0.351 | 0.37 | Y | Y | 0.572 |
| 63931 | CPV Three Rivers Energy Center | 1,221 | 0.352 | 0.412 | Y | Y | 0.57 |
| 62926 | Jackson Generation, LLC | 1,186 | 0.355 | 0.378 | Y | Y | 0.567 |
| 55350 | Dresden Energy Facility | 540 | 0.357 | 0.395 | Y | Y | 0.564 |
| 59326 | Middletown Energy Center | 462 | 0.358 | 0.387 | Y | Y | 0.563 |
| 60357 | Lackawanna Energy Center | 1,362 | 0.359 | 0.374 | Y | Y | 0.562 |
| 50410 | Chester Operations | 56 | 0.359 | 0.359 | — | Y | 0.562 |
| 55990 | Ashtabula | 23 | 0.359 | 0.359 | — | Y | 0.562 |
| 54333 | Bucknell University | 5 | 0.359 | 0.359 | — | Y | 0.562 |
| 62565 | Hill Top Energy Center, LLC | 624 | 0.36 | 0.385 | Y | Y | 0.561 |
| 59906 | Moxie Freedom Generation Plant | 1,045 | 0.36 | 0.379 | Y | Y | 0.56 |
| 59004 | Potomac Energy Center, LLC | 766 | 0.362 | 0.403 | Y | Y | 0.559 |
| 58426 | Hamilton Patriot Generation Plan | 795 | 0.362 | 0.375 | Y | Y | 0.558 |
| 57839 | Woodbridge Energy Center | 726 | 0.362 | 0.383 | Y | Y | 0.558 |
| 60464 | Tenaska Westmoreland Generating  | 947 | 0.363 | 0.392 | Y | Y | 0.558 |
| 59764 | Oregon Clean Energy Center | 817 | 0.363 | 0.384 | Y | Y | 0.558 |
| 60376 | Clean Energy Future-Lordstown, L | 856 | 0.364 | 0.386 | Y | Y | 0.556 |
| 50326 | Nalco | 3 | 0.364 | 0.364 | — | Y | 0.556 |
| 57908 | Central Utility Plant Cincinnati | 46 | 0.364 | 0.364 | — | Y | 0.556 |
| 61028 | Hickory Run Energy Station | 962 | 0.365 | 0.389 | Y | Y | 0.555 |
| 58420 | Hamilton Liberty | 830 | 0.368 | 0.385 | Y | Y | 0.551 |
| 66918 | Trumbull Energy Center | 900 | 0.369 | 0.36 | Y | Y | 0.55 |
| 55939 | Warren County | 1,370 | 0.371 | 0.391 | Y | Y | 0.548 |
| 57794 | St Joseph Energy Center | 715 | 0.371 | 0.384 | Y | Y | 0.547 |
| 60368 | Hummel Station LLC | 1,086 | 0.374 | 0.397 | Y | Y | 0.544 |
| 58079 | Newark Energy Center | 705 | 0.374 | 0.384 | Y | Y | 0.544 |
| 55801 | Marcus Hook Energy LP | 877 | 0.374 | 0.389 | Y | Y | 0.544 |
| 2411 | PSEG Sewaren Generating Station | 541 | 0.374 | 0.396 | Y | Y | 0.544 |
| 58260 | Brunswick County Power Station | 1,376 | 0.376 | 0.4 | Y | Y | 0.542 |
| 55298 | Fairless Energy Center | 1,280 | 0.376 | 0.396 | Y | Y | 0.541 |
| 56807 | Bear Garden | 628 | 0.377 | 0.4 | Y | Y | 0.54 |
| 55667 | Lower Mount Bethel Energy | 602 | 0.377 | 0.399 | Y | Y | 0.54 |
| 55503 | Waterford Power, LLC | 875 | 0.377 | 0.401 | Y | Y | 0.54 |
| 55439 | Tenaska Virginia Generating Stat | 937 | 0.377 | 0.41 | Y | Y | 0.54 |
| 55297 | New Covert Generating Facility | 1,192 | 0.378 | 0.413 | Y | Y | 0.539 |
| 55188 | Cordova Energy | 521 | 0.38 | 0.4 | Y | Y | 0.537 |
| 59220 | Wildcat Point Generation Facilit | 991 | 0.38 | 0.394 | Y | Y | 0.536 |
| 55183 | Nelson Energy Center | 586 | 0.383 | 0.409 | Y | Y | 0.534 |
| 10061 | Mars Wrigley Confectionery US, L | 10 | 0.383 | 0.383 | — | Y | 0.533 |
| 56846 | CPV St Charles Energy Center | 733 | 0.383 | 0.407 | Y | Y | 0.533 |
| 55193 | Ontelaunee Energy Center | 546 | 0.384 | 0.4 | Y | Y | 0.532 |
| 55239 | Red Oak Power LLC | 776 | 0.384 | 0.412 | Y | Y | 0.532 |
| 3804 | Possum Point | 571 | 0.386 | 0.417 | Y | Y | 0.529 |
| 55516 | Fayette Energy Facility | 668 | 0.389 | 0.408 | Y | Y | 0.526 |
| 60302 | Keys Energy Center | 831 | 0.39 | 0.416 | Y | Y | 0.524 |
| 57349 | Garrison Energy Center LLC | 309 | 0.394 | 0.417 | Y | Y | 0.519 |
| 55397 | Washington Energy Facility | 661 | 0.395 | 0.418 | Y | Y | 0.518 |
| 55502 | Lawrenceburg Power, LLC | 1,207 | 0.397 | 0.421 | Y | Y | 0.516 |
| 55231 | Liberty Electric Power Plant | 562 | 0.398 | 0.421 | Y | Y | 0.515 |
| 59773 | Carroll County Energy | 715 | 0.399 | 0.42 | Y | Y | 0.514 |
| 2406 | PSEG Linden Generating Station | 1,300 | 0.404 | 0.418 | Y | Y | 0.508 |
| 55524 | York Energy Center | 1,404 | 0.408 | 0.433 | Y | Y | 0.503 |
| 3797 | Chesterfield | 386 | 0.416 | 0.477 | Y | Y | 0.493 |
| 55736 | Hanging Rock Energy Facility | 1,365 | 0.42 | 0.417 | Y | Y | 0.488 |
| 55131 | Kendall County Generation Facili | 1,140 | 0.423 | 0.431 | Y | Y | 0.485 |
| 2398 | Bergen Generating Station | 1,255 | 0.43 | 0.447 | Y | Y | 0.476 |
| 3176 | Hunlock Power Station | 125 | 0.43 | 0.459 | Y | Y | 0.475 |
| 56963 | West Deptford Energy Station | 736 | 0.431 | 0.429 | Y | Y | 0.475 |
| 55690 | Bethlehem Power Plant | 1,136 | 0.437 | 0.465 | Y | Y | 0.467 |
| 54844 | Gordonsville Energy LP | 218 | 0.453 | 0.48 | Y | N | (0.448) → 0 |
| 10308 | Sayreville Cogeneration Facility | 292 | 0.455 | 0.495 | Y | N | (0.445) → 0 |
| 54832 | Brandywine Power Facility | 427 | 0.457 | 0.483 | Y | N | (0.443) → 0 |
| 50561 | Eagle Point Power Generation | 244 | 0.463 | 0.488 | Y | N | (0.435) → 0 |
| 7153 | Hay Road | 1,098 | 0.476 | 0.493 | Y | N | (0.419) → 0 |
| 10751 | Camden Plant Holding LLC | 173 | 0.48 | 0.557 | Y | N | (0.415) → 0 |
| 52019 | Doswell Energy Center | 702 | 0.487 | 0.515 | Y | N | (0.406) → 0 |
| 55701 | Fremont Energy Center | 685 | 0.507 | 0.4 | Y | N | (0.382) → 0 |
| 10030 | Energy Center Dover | 59 | 0.515 | 0.398 | Y | N | (0.372) → 0 |
| 55710 | Allegheny Energy Units 3 4 & 5 | 556 | 0.528 | 0.359 | Y | N | (0.357) → 0 |
| 55337 | Ironwood LLC | 760 | 0.606 | 0.418 | Y | N | (0.262) → 0 |
| 55976 | Hunterstown Power Plant | 810 | 0.607 | 0.408 | Y | N | (0.26) → 0 |
| 58207 | Central Utility Plant at White O | 24 | 0.622 | 0.622 | — | N | (0.242) → 0 |
| 10633 | Hopewell Cogeneration | 378 | 0.645 | 0.439 | Y | N | (0.214) → 0 |
| 10805 | Kenilworth Energy Facility | 24 | 0.658 | 0.404 | Y | N | (0.197) → 0 |
| 2393 | Gilbert | 302 | 0.679 | 0.84 | Y | N | (0.172) → 0 |
| 3096 | Brunot Island | 244 | 0.679 | 0.657 | Y | N | (0.172) → 0 |
| 58933 | Shell Chemical Appalachia LLC | 257 | 0.685 | 0.591 | Y | N | (0.164) → 0 |
| 55216 | Morris Cogeneration LLC | 194 | 0.729 | 0.361 | Y | N | (0.111) → 0 |
