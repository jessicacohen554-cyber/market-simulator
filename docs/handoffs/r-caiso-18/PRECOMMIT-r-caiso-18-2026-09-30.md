# PRECOMMIT R-CAISO-18 — fold CC_REGULAR over-dispatch 2019–21 (2026-09-30)

Written before any solve. Owner card 2026-09-30: "Fold CC over-dispatch".
Incumbent keeper `2026-09-30-caiso-r17-earlyclock` (bundle `rcaiso17_A_span`, 2022–25, CALIBRATED, single
ledgered C3c 2024). Fold `-touchpoints` (bundle `rcaiso17_A_tp_2019_2021`, NOT-YET, reported only, rule 30(c)).

## 1. Attribution (zero LP)

The balance identity is gas = total supply − imports − non-gas. Actuals are the CAISO Outlook 5-minute fuel-source
series (`data/raw/caiso-outlook-fuelsource`), which is the ISO's own measured record. Model values come from the
fold payload. Units are TWh.

| | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| Outlook gas / model gas family | 65.0 / 75.0 | 73.8 / 84.9 | 79.2 / 76.8 |
| Outlook imports / model imports | 51.6 / 38.1 | 56.4 / 38.9 | 50.5 / 46.3 |
| EIA-930 CISO net import (TI) | 53.8 | 59.4 | 54.4 |
| DSW corridor, model / EIA-930 | 21.3 / 44.7 | 17.4 / 42.0 | 29.7 / 40.9 |
| PNW corridor, model / EIA-930 | 16.8 / 9.2 | 21.5 / 17.4 | 16.6 / 13.6 |
| Non-gas in-state, model − Outlook | +1.2 | +0.6 | +0.2 |
| Total supply, model − Outlook | −2.2 | −5.8 | −6.3 |
| **C1 CC_REGULAR, model − EIA-923** | **+23.1** | **+25.3** | **+10.5** |

**Actual basis: not the cause.**
- EIA-930 CISO NG gas equals the Outlook gas (65.2 / 73.8 / 79.3).
- The gap between that series and the rubric's EIA-923 grid-delivered gas family is steady at 14.2 / 14.6 / 13.9 /
  14.9 TWh over 2019–22. The keeper's first year, 2022, passes on the same basis.
- A basis shift specific to the fold years would show up as a change in that offset. It does not.

**Demand, hydro, solar/wind, nuclear, other: not the cause.**
- Each is within ±2 TWh of the Outlook. Model hydro 29.2 / 16.2 / 11.4 is at or above the measured value, so it
  pushes gas down, not up.

**Fleet: not a balance term.**
- CC_REGULAR membership and capacity move the CC/CT split, not total gas. The model's CT/ST classes are near or
  above actual, so the CC excess is not a CT→CC substitution.

**The model is over-dispatching, and the displaced supply is DSW imports.**
- The DSW deficit is −23.4 / −24.6 / −11.2 TWh. That matches the CC excess one-for-one, as R-CAISO-12 §4 found
  and R-CAISO-7 before it. PNW over-imports.

**Mechanism.** Taken from the R-CAISO-17 legs' P1 dispatch (leg commits `3101bb74`, `0eda8f1b`, `3e9d2682`,
provenance only).

| DSW tranche, TWh | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| DSW_solar_PV (firm, shaped) | 19.5 | 17.3 | 12.6 |
| DSW_CCGT / DSW_CT (ladder $68 / $110) | 1.2 / 0.7 | 0.07 / 0.0 | 1.0 / 0.3 |
| clean rungs (measured-hub-armed) | 0 | 0 | 15.8 |

- In 2019–20 there is no measured intertie hub price. OASIS GroupZip's earliest trade date is 2021-04-27 (per the
  `lmp-data/CAISO` README), so `measured_import_hub_prices` returns None.
- The DSW gas blocks therefore sit on the static Tier-3 ladder, labelled "static-fitted-pending-measured" in
  `interchange/spec.py`, against a CAISO λ of about $36–41 mean. They barely run.
- In 2021, Jan–Apr is unprinted, so the same thing happens for those four months.

## 2. New evidence (why this is not a re-test of the 2019–20 STOP)

R-CAISO-7 and R-CAISO-12 closed the 2019–20 hub-price route on two grounds:
1. The measured-gas reference formula "prints no value for most 2019–21 state-months".
2. The ICE daily index needs a per-year fitted basis.

**Ground 1 is an EIA withholding, and it can be reconstructed with zero parameters.**
- N3045AZ3 and N3045OR3 are withheld for 2019–21. The EIA-923 Schedule 2 plant receipts that EIA aggregates into
  N3045 are committed (`_processed-legacy/eia923_monthly_fuel_costs.parquet`).
- AZ has 17 plants reporting, 12/12 months, every year 2018–25. OR has 6 plants, 12/12 months.
- Where N3045 prints, the quantity-weighted rebuild reproduces it:

| State | Months | r | Mean (rebuild − N3045), $/MMBtu | MAE |
|---|--:|--:|--:|--:|
| AZ | 47 | 0.980 | −0.21 | 0.28 |
| OR | 36 | 0.975 | +0.47 | 0.59 |

**Validation of the resulting 2019–20 hub level against ICE (check only, never an input).**
- Measured on ICE on-peak days (HE7–22, Mon–Sat).
- ICE workbooks: `eia.gov/electricity/wholesale/xls/archive/ice_electric-<y>final.xlsx`.

| Palo Verde, $/MWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|--:|--:|--:|--:|--:|--:|
| ICE on-peak mean | 33.3 | 52.9 | 64.8 | 99.6 | 76.2 | 39.5 |
| formula − ICE | −4.4 | −22.3 | −0.1 | +5.8 | −18.7 | −10.7 |
| OASIS − ICE (R-CAISO-12) | — | — | −17.1 | −11.9 | −18.0 | −8.1 |
| static DSW_CCGT ladder − ICE | +34.7 | +15.1 | | | | |

- The 2019–20 formula errors lie inside the formula's own out-of-sample range (−18.7 … +5.8).
- The static ladder is above ICE, and ICE itself runs above the intertie DAM by 8–18.
- **Rule 14:** a measured-input estimate beats a static fitted proxy.
- **Rule 13:** the formula is the forecast's own hub construction (`caiso_hub_reference_price`) with measured gas in
  place of the forward Henry Hub, so it regenerates for a forward year.
- No fitted basis, no per-year value.

## 3. The build (one flag, zero parameters)

The flag is `caiso_intertie_unprinted_year_measured_gas`: default off, CAISO-only, backcast-only, per-hub topology.

- **Loader** (`eia930/envelopes.measured_import_hub_prices`):
  - Scope: a hub whose gap is more than 25 %, including a year the OASIS extract does not carry at all.
  - Its unprinted hours take the measured-gas reference formula (`neighbor_price.caiso_hub_measured_gas_reference_price`).
  - Its gas operand takes `eia923_fallback=True`: a month N3045 withholds uses the EIA-923 rebuild
    (`fuel/electric_power.state_electric_power_monthly_gas_eia923`), and a printed month is never replaced.
- **Untouched:**
  - the forward Henry Hub fill, and its ≤25 % bound on a forecast estimate inside a backcast year;
  - the ≤25 % path;
  - the clean-depth arming, which still reads only the raw print (`measured_intertie_hub_price_raw`).
- **Consumers:**
  - the per-hub injector;
  - `_caiso_measured_hub_unprinted_masks`, so the ladder-only gas coupling skips the newly hub-priced hours rather
    than double-counting gas (the R-CAISO-3 defect).
- **Zero-LP check on committed data:**
  - 2022–25 loader output is **byte-identical**.
  - 2019 and 2020 now return every tranche at 8,760 finite hours: DSW mean $28.12 / $30.03, Malin $34.00 / $31.49.
  - 2021 fills Jan–Apr: DSW_CCGT 5,976 → 8,760 finite hours, annual mean $55.05.

## 4. Shards (rule 36)

- Seven shards, one per year 2019–2025. The recipe is the keeper recipe with `--set
  caiso_intertie_unprinted_year_measured_gas=true`.
- `{SRC}` is `rcaiso17_A_tp_2019_2021` for 2019–21 and `rcaiso17_A_span` for 2022–25.
- The SHA is pinned after the build PR merges. The parent never solves (rule 32(a)).
- G-DRIFT: the build touches the loader, the formula, the fuel module, the injector and mask signatures, the runner
  pass-through and the field. Every one is inert when the flag is off, and inert in 2022–25 when it is on (§3). No
  control solve is spent (rule 29(b)).
- New hard stop, the loader probe with the keeper's hub kwargs. It must print, for DSW_CCGT finite hours and mean:
  - 2019 `8760 28.12`;
  - 2020 `8760 30.03`;
  - 2021 `8760 55.05`;
  - 2022 `8760 82.95`;
  - 2023 `8760 57.67`;
  - 2024 `8760 33.34`;
  - 2025 `8760 32.47`.

## 5. Predictions (direction and rough size; first-order, no price feedback)

- 2019 and 2020:
  - DSW import up by roughly +10 to +25 TWh;
  - CC_REGULAR down by a similar amount;
  - SP15 mean price down;
  - PNW roughly unchanged (Malin formula $31–34 against the $36 ladder).
- 2021:
  - a smaller move, confined to Jan–Apr;
  - the formula carries the measured Feb-2021 AZ gas spike.
- 2022–25:
  - identical to the incumbent (max |Δ class TWh| = 0.0000).

## 6. Decision rule (pre-registered)

**PROMOTE on structure (rule 14)** if both of these hold:
- (a) The 2022–25 legs reproduce the incumbent: max |Δ class TWh| = 0.0000, and the span stays CALIBRATED.
- (b) The repair is complete: every leg passes the §4 hard stop, and every 2019–21 leg logs the per-hub intertie
  pricing.

The fold's movement is **reported**, not gated. The fold can never downgrade the ISO (rule 30(c)).

**Structural backstop, declared now and not a fit gate.** The build must not create the opposite structural error
at a larger size.
- The trigger: in any fold year, the model's DSW net import overshoots EIA-930 by more than the pre-build deficit,
  so |DSW error| grows.
- If that happens, the trade goes to the owner as a decision card instead of an automatic promotion.
- Otherwise (a) and (b) decide.
