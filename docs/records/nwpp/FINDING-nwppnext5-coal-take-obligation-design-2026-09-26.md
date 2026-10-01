# FINDING — NWPP-NEXT-5 phase 0: coal period fuel-take obligation, census and design (ZERO LP)

**Question.** RESULT-nwppnext4 §3 proposed that NWPP coal runs under a **period fuel-take obligation**, and that the
obligation would act as an energy budget shaped into the best hours. Would an admissible, prior-year-identified
obligation repair C4 coal hourly r (keeper #11: 0.697 / 0.749 / 0.706 / 0.753 / 0.670 / 0.593 / 0.668; floor 0.70)?

**Answer: no.** An obligation of this kind is admissible and structurally real, and it is a coal **volume** lever. It
is not a **shape** lever:

- In 2023, the year the lane cares about most, it barely binds.
- Every price-shaped emulation lowers C4 r.
- The best bracket (no reshaping) moves r by at most +0.06, and 2023–25 still fail.

**Artifacts** (nothing solved, nothing committed):
- Probe: `scripts/probes/_nwppnext5_coal_contract_census.py`.
- Output: `results/calibration/_nwppnext5_coal_contract_census.json`.
- Inputs:
  - `data/raw/coal-receipts` (EIA-923 Page 5) and `data/raw/coal-stocks` (Page 2).
  - Keeper #11 `nwppnext4_span/hourly/{class,class_band,system}_<y>.parquet`.
  - Keeper #10 per-plant census `_nwppnext4_coal_census.json`.
  - The EIA-930 pool series (`_pool_hourly_benchmark`). Keeper #11's r is reproduced exactly in every year.

## 1. Estimators (rule 13: only year ≤ Y-1 rows size year Y)

| Tag | Obligation for solve year Y | Rationale |
|---|---|---|
| **A** | Y-1 contract tons (Purchase Type C/NC/T) whose `Contract Expiration Date` falls in Y or later. Pro-rated by the months of Y the contract covers. | Contracts demonstrably in force |
| **B** | All Y-1 contract tons | Assumes renewal at the same volume. Renewals are invisible ex ante, and A misses them. |
| **A_net / B_net** | `max(0, take + Dec(Y-1) stock − max month-end stock over 2018..Y-1)` | The **burn** floor the take implies once the yard can absorb tons into its pile (the pile's own measured ceiling) |

Conversion for every estimator:
- Tons → MMBtu at the Y-1 lot heat content.
- MMBtu → MWh at the model's own `measured_coal_heat_rates`. That is the coefficient a `Σ HR·P ≥ budget` row would
  carry.

Undated contract lots (Sunnyside waste coal, T type) are reported and excluded. Same-year receipts appear only as an
`outcome_not_admissible` column.

**Supply structure** (Y-1 = 2023 receipts; the pattern holds in all years):

| Plant | Contract share | Mine-mouth (TC conveyor) share | Contract expiry (share of tons) |
|---|---|---|---|
| Colstrip 6076 | 1.00 | 1.00 (Rosebud) | 2025: 100 % |
| Naughton 4162 | 1.00 | 1.00 (Kemmerer) | 2025: 100 % |
| Wyodak 6101 | 1.00 | 1.00 | 2026: 100 % |
| Jim Bridger 8066 | 1.00 | 0.57 (Bridger Coal) | 2023: 43 %, 2024: 57 % |
| Hunter 6165 | 0.89 (spot 0.11) | 0 (truck; Sufco / Emery / Bear Canyon) | 2023: 56 %, 2024: 30 %, 2025: 14 % |
| Huntington 8069 | 1.00 | 0 (truck; Skyline / Sufco) | 2029: 100 % |
| Bonanza 7790 | 1.00 | 0 (rail from affiliate Deserado, Blue Mountain Energy) | 2025: 100 % |
| Dave Johnston 4158 | 1.00 | 0 | 2024: 96 % |
| Centralia 3845 | 1.00 | 0 | 2025: 84 % |
| North Valmy 8224, TS Power 56224 | 1.00 | 0 | 2023–24: ~100 % |

What the table shows:
- **NWPP coal is ~100 % contract, and four plants are captive mine-mouth.** A take obligation is real.
- **Expiry dates are one to two years out and roll forward every year**, so A under-reads systematically. For
  example, it gives Hunter 2021 **0.45 TWh** against 7.27 TWh received, and Jim Bridger and Dave Johnston 2025 **0**.
- Delivered cost: Hunter 182 → 266 → 345 ¢/MMBtu for receipt years 2022 → 2024, which confirms the §3 premise.

## 2. Does the obligation bind? (TWh; keeper #11 per-plant energy is estimated from #10's plants scaled by class)

| Year | Keeper #11 coal | EIA-930 coal | CAMPD gross | Same-yr receipts (outcome, not admissible) | A | **A binds** (n plants) | B | **B binds** (n) | A_net binds | B_net binds |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 52.14 | 54.55 | 66.76 | 62.55 | 47.37 | **5.25** (6) | 59.06 | **11.03** (9) | 4.54 | 9.35 |
| 2020 | 39.11 | 51.94 | 54.46 | 53.59 | 35.30 | **6.54** (5) | 60.78 | **23.08** (10) | 5.13 | 19.81 |
| 2021 | 53.13 | 50.14 | 57.55 | 49.17 | 33.78 | **1.00** (3) | 51.32 | **5.23** (6) | 0.57 | 3.83 |
| 2022 | 60.48 | 49.41 | 57.39 | 48.85 | 40.82 | **0.41** (2) | 48.47 | **0.84** (3) | 0.10 | 0.49 |
| 2023 | 47.34 | 42.27 | 48.10 | 42.35 | 37.66 | **1.81** (2) | 46.68 | **3.85** (3) | 1.11 | 2.04 |
| 2024 | 29.43 | 38.30 | 40.21 | 40.35 | 33.92 | **8.32** (5) | 41.75 | **13.30** (9) | 5.90 | 8.67 |
| 2025 | 31.52 | 42.26 | 45.86 | n/a (no 2025 923) | 27.29 | **5.81** (4) | 40.68 | **10.73** (8) | 3.23 | 5.56 |

**Which plants bind under A:**
- 2023: Colstrip +1.29 and TS Power +0.52 only. Utah BIT does not bind: in 2023 Hunter and Huntington run *above*
  CAMPD in the model.
- 2024: Colstrip +3.22, Centralia +3.13, Bonanza +1.39.
- 2025: Huntington +1.97, Centralia +1.73, Bonanza +1.48.

**Estimator B as an admissible level predictor.** Against the same-year outcome it lands within ~10 % in 2020–24
(59.1 / 60.8 / 51.3 / 48.5 / 46.7 / 41.7 vs 62.5 / 53.6 / 49.2 / 48.9 / 42.4 / 40.4). It would close the 2020 / 2024 /
2025 coal-short **volume** gaps (−12.8 / −8.9 / −10.7 TWh vs EIA-930). That is a real, separate finding.

## 3. Zero-LP C4 coal r prediction on keeper #11's hourly data

How the emulation works:
- Per coal class and period, each plant's deficit (obligation − model, never netted against another plant's surplus)
  goes into the class's highest model-price hours. Price is the cap-weighted zonal price.
- Headroom is capped by the plants' mean available cap.
- `eq` also removes surplus from the lowest-price hours, down to the must-run band. That is a budget **equality**.
- `prop` spreads the deficit pro rata on the class's own shape. It is the no-reshaping bracket, and the one closest to
  full price feedback.
- The price-taker `floor` is the opposite bracket: an LP with an energy row fills whole bands in the top hours, and
  only price feedback spreads it. The truth lies between the two brackets.

| Year | Keeper #11 r | A yr-floor | A yr-prop | A mo-floor | A yr-eq | B yr-floor | B yr-prop | B_net yr-floor | Coal TWh A yr-floor / B yr-floor (EIA-930) |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | 0.697 | 0.653 | 0.713 | 0.516 | 0.524 | 0.547 | 0.730 | 0.563 | 57.4 / 63.2 (54.6) |
| 2020 | 0.749 | 0.634 | 0.753 | 0.549 | 0.628 | 0.565 | 0.729 | 0.608 | 45.6 / 61.7 (51.9) |
| 2021 | 0.706 | 0.669 | 0.706 | 0.664 | 0.522 | 0.646 | 0.705 | 0.669 | 54.1 / 57.7 (50.1) |
| 2022 | 0.753 | 0.746 | 0.752 | 0.755 | 0.483 | 0.730 | 0.752 | 0.745 | 60.9 / 61.3 (49.4) |
| 2023 | **0.670** | 0.611 | 0.674 | 0.508 | 0.345 | 0.573 | 0.677 | 0.602 | 49.1 / 51.2 (42.3) |
| 2024 | **0.593** | 0.606 | 0.629 | 0.494 | 0.614 | 0.528 | 0.650 | 0.595 | 37.8 / 42.7 (38.3) |
| 2025 | **0.668** | 0.531 | 0.674 | 0.563 | 0.378 | 0.613 | 0.666 | 0.496 | 37.3 / 42.2 (42.3) |

**Why it does not help:**
1. **Real coal does not swing with the model's price.** r(EIA-930 coal, load-weighted model price) is only
   0.10 / 0.29 / 0.16 / 0.19 / 0.32 / 0.16 / 0.15. A budget dual shapes coal onto the model's price, so it adds energy
   exactly where the actual swing is *not*. The annual price-taker floors lose up to 0.18 r; the single gain is A 2024
   at +0.013. The equality variants, which also strip low-price hours, lose up to 0.44.
2. **The 2023 miss is not a shortfall.** Only 1.8 TWh binds under A and 3.8 TWh under B, and the model is already
   +5.1 TWh long against EIA-930.
3. **A monthly period is worse than an annual one** in 5 of 7 years under A and 6 of 7 under B. A uniform monthly take forces coal into the
   spring hydro months, where real coal backs down.
4. **The best case, no-reshape B, still fails.** It gives 2023 0.677, 2024 0.650 and 2025 0.666, all below 0.70.

NRMSE was not recomputed; r alone decides the question.

## 4. Design, if the mechanism is armed on its own structural merits (rules 1 and 14, not C4)

**What `coal_fuel_inventory` is.** It is a coal fuel **CEILING**, built for miso-259/268 in
`data/coal_fuel_inventory.py` and `lp/rows.py::_build_oil_budget_rows`:
- The row is `Σ HR·P ≤ (Dec(Y-1) stock + mean Y-2..Y-1 receipts) × heat content`.
- Two limbs: pooled monthly (`budget/12`) and per-yard annual (`_plant_grain`).
- It is the missing-limb *cap* on coal. It is not a take floor.

**Why it raises outside MISO.** `run_calibration.resolve_coal_budget_arms` evidence-gates it under rule 25:
- The pooled limb is MISO-only, because its /12 month grain was identified on MISO.
- The yard limb is limited to `COAL_PLANT_GRAIN_ISOS = (MISO, NEISO)`.
- It is also backcast-only, because a forecast needs the model's own carried stock.

The construction itself is ISO-generic. Every sizing quantity is the yard's own EIA-923 record.

**Recommended form: generalise, do not add a row family (rule 19).** The per-yard annual row gets a **lower bound**
beside its existing upper bound:

  `take_net(Y) ≤ Σ_{g∈yard} HR_g · P_{g,t} summed over the year ≤ stock(Y-1) + receipts rate`

where `take_net = max(0, in-force contract tons + Dec(Y-1) stock − max prior month-end stock) × hc`.

Why this form:
- It is one identity, `burn = opening + receipts − closing`, with each side bounded by measured prior-year quantities.
- The builder already emits `(row_lower, row_upper)`, so the change is a lower-bound vector rather than a new family.
- The row dual is the take-or-pay shadow price, λ ≥ 0 when the floor binds. Every band's effective offer drops by
  `HR·λ` only when the obligation would otherwise go unmet. That is exactly the "sunk over the period, marginal only if
  unmet" logic `coal_committed_takeorpay_sunk_fixed` already states in prose.

**Rule 19 reconciliation, which is mandatory because the incumbents already floor coal:**

| Incumbent (keeper #11) | What it does | Under the period row |
|---|---|---|
| `coal_takeorpay_from_data` | Must-run band bids `(1 − contract_share)` fuel, so ~VOM for NWPP's ~100 % contract plants. This is a per-hour take-or-pay proxy. | **Replace.** The contract is carried once, by the row's dual. The band reverts to physical min-stable at full cost. |
| `coal_committed_takeorpay_regulated` | Committed band gets the sunk-fuel discount for regulated (all PacifiCorp) plants | **Replace** (arm `coal_committed_takeorpay_sunk_fixed`, or drop the flag) |
| `coal_committed_nested_on_mustrun`, CAMPD must-run p10 | Physical minimum load | Keep. It is physics, not contract. |

**Free parameters: zero.**
- Take comes from 923 Page 5 at Y-1.
- The stock ceiling is the 923 Page 2 maximum at ≤ Y-1.
- Heat content and heat rate are measured.
- The choice of estimator (A vs B) and period (annual) is structural, and is fixed ex ante by the owner, never by the
  gates.

**Forward story (rule 13).** For forecast year Y, the take is the then-latest 923 contract tonnage in force at Y,
decayed as contracts reach their filed expiry. Under B it is renewed at volume until the plant's step-0/1b exit date.
The stock term is the model's own carried inventory, the same carry the ceiling already needs. The take responds to
changed conditions through expiry, retirement and exits. Under A, a forward year beyond the filed expiry carries
**zero** obligation. That is honest, but it is why A under-reads, and why A vs B is a real owner choice.

**Predicted consequence if armed** (annual, `_net`, per yard):
- Coal volume rises toward EIA-930 in 2020 and 2024–25, by +3–9 TWh of binding.
- It is inert in 2022, and nearly inert in 2021 and 2023.
- **C4 r is flat to −0.1.** Arm it for rule 14 on its own evidence, never as a C4 fix.

## 5. Owner questions

- **Q1.** Is the mechanism a generalisation of `coal_fuel_inventory_plant_grain` (a lower bound on the existing yard
  row, adding NWPP to its ISO gate on this census as NWPP's own evidence), or a new coal take-obligation row family?
  *Recommend: generalise.* One identity, one row family (rule 19).
- **Q2.** Should the period be annual or monthly? *Recommend: annual.* A uniform monthly take is worse in 5–6 of 7 years
  and has no monthly contract data behind it. EIA-923 carries no monthly minimum.
- **Q3.** Should the take be a floor (`≥`) or a budget equality (`=`)? *Recommend: floor.* Equality forces over-take
  plants down to their contract, which costs up to 0.44 r and pins burn to a receipt quantity. That is too close to the
  rule-13 outcome.
- **Q4.** Which estimator: A (in force at Y, zero after the filed expiry) or B (Y-1 volume, assumed renewed)? And is
  the `_net` stock-slack adjustment adopted? A under-reads through rolling one-to-two-year expiries. B embeds a renewal
  assumption.
- **Q5.** Should the incumbent per-hour take-or-pay discounts (`coal_takeorpay_from_data` and
  `coal_committed_takeorpay_regulated`) be retired in the same arm, as rule 19 requires?
- **Q6.** C4 coal is still open. r(actual coal, model price) ≤ 0.32 in every year, so neither a price-shaped nor a
  budget mechanism can reach it. Does the lane pivot to *what* real NWPP coal swings with, or accept C4 coal as
  ledgered?
