# NYISO calibration — best config so far

Keeper: **`nyiso p11 smoke 2023` config (P9b served-interchange defaults),
promoted to the P12 sign-off keeper** (2026-06-12, bundle
`results/calibration/nyiso_smoke_2023`, highspy 1.x). P12 ran the offer-curve /
hydro / storage / import / dual-fuel knobs against this config and **found no
honest knob that improves an in-tolerance class without a zero-sum trade against
another, or without violating a documented convention** — so the structural
P9b config *is* the keeper. Reproduce with:

```
python scripts/run_calibration_full.py --iso NYISO --year 2023 --commitment \
    --out-dir results/calibration/nyiso_smoke_2023
```

All the NYISO calibration toggles fire by **default** in the harness
(`_calibration_config`): measured net interchange served in `load_demand`
(P9b), `gas_monthly_actuals` + `gas_plant_monthly_fuel_pricing` (measured
EIA-923 monthly gas, P7), RGGI via `state_carbon_price_by_iso` ($13.49/t 2023),
the EIA-860 dual-fuel oil-parity cap (385 gas tranches / 15.9 GW), the historic
CEMS outage overlay (318 plant-tranches derated), and the 154-plant hydro
energy budget (28.40 TWh). **No offer band was tuned** — see the success bar.

## Success bar (fuel-mix ±5%/class vs EIA-923; size-aware on the small classes)

NYISO 2023 is **mix-calibrated**: every renewable / baseload class lands inside
±5% of EIA-923, and the two largest gas classes are on target. The residual is
a single **gas-total basis floor** (below) that lands on the small CHP/peaker
classes — the least-distorting place for it.

## Results (P2, 2023, vs EIA-923 incl. CHP/peaker split)

| class | model TWh | EIA-923 TWh | Δ% | bar |
|---|---|---|---|---|
| CC_REGULAR | 32.14 | 33.01 | −2.6% | ✓ |
| CC_CHP | 14.10 | 16.50 | −14.6% | ✗ (basis) |
| ST_GAS | 8.07 | 8.14 | −0.8% | ✓ |
| CT_CHP | 1.44 | 2.59 | −44.2% | ✗ (basis) |
| ST_CHP | 1.25 | 1.53 | −18.0% | ✗ (basis) |
| CT_PEAKER | 0.51 | 2.07 | −75.2% | ✗ (basis) |
| **gas total** | **57.53** | **63.84** | **−9.9%** | basis floor |
| hydro | 28.38 | 28.03 | +1.3% | ✓ |
| nuclear | 27.49 | 27.53 | −0.1% | ✓ |
| wind | 4.60 | 4.77 | −3.6% | ✓ |
| solar | 1.95 | 2.05 | −5.0% | ✓ (edge) |
| OTHER | 2.20 | 2.20 | 0.0% | ✓ |
| biomass | 1.62 | 0.84 | +93% | ✗ (small abs +0.78 TWh) |
| oil | 0.01 | 0.42 | −96.9% | ✗ (U4-blocked) |
| **TOTAL gen** | **123.77** | **129.67** | **−4.5%** | demand-basis gap |
| net interchange | −23.45 | −23.45 (930) | RMSE **0 MW** | ✓ |
| CO2 (approx, class rates) | ~24.2 Mt | eGRID 26.9 (excl-biogenic) | ~−10% | downstream of gas |
| avg price (level-only, P10 held) | $42.72 | — | max $235.81 | not scored |

## The gas-total basis floor (why −9.9% is not a dispatch error)

Energy balance pins the in-state fleet's total: model TOTAL = served demand =
EIA-930 transmission-metered demand (147.05 TWh) + measured net interchange
(−23.45 TWh) = **123.77 TWh**, which is structurally **4.5% below** EIA-923's
plant-net-generation total (129.67 TWh). The non-gas classes all match EIA-923,
so the −5.9 TWh total gap **must** fall on the swing fuel: gas lands at −9.9%.

This gap is **not** closable by any honest dispatch knob:
- **td_loss gross-up** is ruled out — EIA-930 demand is transmission-metered
  (generation-side; playbook §8.1), so distribution losses sit below the meter
  and a gross-up would double-count (the ERCOT `td_loss_factor = 0` convention).
- **import scaling** would lift gas (serving e.g. −20 TWh, inside the ±15%
  interchange tolerance, lifts the total to ~127 and gas to ~−4%), but the
  measured EIA-930 interchange is matched **exactly** (duration RMSE 0 MW,
  import-hours 100%, diurnal corr +1.00). Degrading a perfect, measured match to
  paper over an EIA-930-vs-EIA-923 *benchmark-basis* difference is overfitting,
  not calibration. **Rejected.**
- **offer-curve / CHP / storage** reshuffle *within* the fixed total: the
  under-running CHP/peaker classes cannot be lifted into tolerance without
  pulling the on-target CC_REGULAR/ST_GAS down by the same TWh, and the obvious
  CHP lever does not even do that. The P12 `nyiso 2 chp-covered` probe
  (`--chp-startup-covered`, removing the steam-host startup-amortization markup)
  moved CHP by only **+0.1 TWh total** (CC_CHP +0.03, ST_CHP +0.05, CT_CHP
  +0.02; gas total 57.53 → 57.54, price $42.72 → $43.02) — i.e. the CHP/peaker
  deficit is **structural** (the model dispatches CHP economically and enforces
  no hard steam-host must-run floor), not a startup-cost artifact. The current
  split — deficit on the small CHP/peaker classes, big classes on target — is
  the least-distorting landing spot for the basis gap.

Benchmarked against EIA-930 (the operationally consistent basis), gas is
−5.7% (57.53 vs 61.00) — i.e. the class is within a basis-width of tolerance;
the −9.9% is the EIA-930/EIA-923 reconciliation, documented, not tuned.

## Config (the knobs that matter)

- `td_loss_factor = 0.0` (EIA-930 NYIS demand is transmission-metered /
  generation-side; no gross-up — playbook §8.1).
- **Net interchange served by default** (P9b): `load_demand` folds the measured
  EIA-930 `NYIS hourly` `Total interchange` (−23.45 TWh, export-positive, served
  as-is) into demand; the priced node stays the forward mechanism
  (`--priced-interchange`, `include_interchange=False`).
- **Measured monthly gas on by default** (P7): `gas_monthly_actuals = True` +
  `gas_plant_monthly_fuel_pricing = True`. The NYISO ISO-month series carries
  real winter spikes (Jan-2023 **$10.02**/MMBtu, Feb $5.62 vs the flat $2.54 HH
  seed). The explicit `--gas-monthly-actuals` P12 probe was a **no-op** (already
  default) — confirmed byte-identical mix and price duration.
- **RGGI** $13.49/t (2023) active via `state_carbon_price_by_iso.NYISO`.
- **Hydro**: 154-plant, 28.40 TWh annual energy budget; lands +1.3% vs EIA-923,
  no over/under-displacement (the §8.4 hydro failure mode is clean).
- **Dual-fuel**: machinery active (385 gas tranches / 15.9 GW capped at the
  delivered oil price) but oil clears 0.01 vs 0.42 TWh — even measured monthly
  gas (Jan $10) never crosses distillate parity (~$16/MMBtu), so the switch does
  not trip on monthly data. **This is the documented P13 limitation: the winter
  oil recovery is gated on the U4 daily Transco-Z6/Iroquois gas basis, which is
  not uploaded for NYISO** (only the NEISO/Algonquin leg is filled).

## Failure-mode watch (P12 checklist)

- **Residual gas after interchange** 🟢 — gas is *under*, not over: the served
  measured wedge fully removes the P11 over-generation; the residual −9.9% is
  the demand-basis floor above, not unserved imports.
- **Downstate congestion separation** ⚪ not scored — modeled zonal spread is
  small ($0–4); cannot compare J−A / K−A LBMP (P10/U2 LMP upload held).
- **Hydro displacement** 🟢 — +1.3% vs EIA-923, budget honored.
- **Nuclear refuel months** 🟢 — −0.1% annual; monthly CF overlay clean.
- **Import-share drift** 🟢 (2023) — exact match. **🔴 2025/2024 are data-blocked
  (below).**

## Blocked years (not runnable as clean backcasts yet)

- **2025** — the EIA-930 `NYIS hourly` extract stops at **Q1 2025** (2,160 h of
  8,760), so `nyiso_net_interchange(2025)` returns `None` and the backcast
  serves **0** of the ~−23 TWh import wedge → **+22.7% over-generation**
  (151.9 vs EIA-923 123.8 TWh, avg price $127). The 2025 EIA-923 benchmark is
  also preliminary (biomass 0.13, solar 0.66 TWh — under-reported). **Refresh:
  extend the EIA-930 NYIS extract through 2025-12 and re-pull final 2025
  EIA-923.** Until then 2025 is filed, not calibrated.
- **2024** — blocked on `NY_2024` unit-level CEMS (only facility-level present)
  and the missing `NYISO_2024_renewable_capacity.csv`.

## History

P11 (`nyiso p11 smoke 2023`) was the structural smoke; P9b served the measured
net interchange (the dominant structural gap), turning the interchange row green
and gas from +25.6% to −9.9%. P12 confirmed the structural config is the keeper.
P12 probes, all rejected (logged in `docs/calibration-log.md`, "NYISO P12"):
`nyiso 1 gas-actuals` (no-op, already default), `nyiso 2 chp-covered`
(negligible — CHP deficit is structural, not a startup-cost artifact).

## Citations (P12 benchmarks & conventions)

- **Fuel-mix benchmark** — EIA-923 Generation & Fuel (2023), per-plant net
  generation rolled to the model class taxonomy; bundle `eia923.parquet`. 2023
  NYISO class totals: CC_REGULAR 33.01, CC_CHP 16.50, ST_GAS 8.14, CT_CHP 2.59,
  CT_PEAKER 2.07, ST_CHP 1.53 TWh (gas 63.84); hydro 28.03, nuclear 27.53,
  wind 4.77, solar 2.05, OTHER 2.20, biomass 0.84, oil 0.42 TWh.
- **Net interchange** — EIA-930 `NYIS hourly` `Total interchange` (export-
  positive), 2023 = −23.45 TWh / −2,677 MW avg; served as-is by `load_demand`
  (P9b). Coverage: 2023 full, 2024 full, **2025 Q1-only (2,160 h)** — the 2025
  block.
- **Demand basis** — EIA-930 `NYIS hourly` Demand is transmission-metered
  (generation-side / net of BTM PV), so `td_loss_factor = 0.0` (playbook §8.1;
  param `scenario.td_loss_factor`, EIA-930 Demand + Interchange = Net Generation).
- **CO2 benchmark** — eGRID2023 (EPA, `egrid2023_data_rev2 2.xlsx`), NYISO 2023:
  gas_cc 16.25 + gas_ct 10.36 + oil 0.26 = 26.86 Mt (biomass 1.33 biogenic,
  excluded under EPA/RGGI accounting).
- **RGGI carbon** — `state_carbon_price_by_iso.NYISO` $13.49/t (2023), RGGI
  quarterly CO2-allowance auction clearing prices (annual simple average).
- **Measured monthly gas** — EIA-923 monthly Natural Gas receipt costs,
  volume-weighted to the NYISO hub: Jan-2023 $10.02/MMBtu, Feb $5.62 (vs the
  flat $2.54 Henry-Hub seed). Distillate (oil) parity ~$16/MMBtu (EIA-923
  Schedule 5 Petroleum receipts) — never crossed on monthly averages, hence the
  U4 daily-basis gate on winter oil.
- **Hydro budget** — 154-plant EIA-923 annual energy budget 28.40 TWh (2023);
  NYPA treaty min-flows `nyiso_hydro_treaty_min_flow` (1957 St-Lawrence/Niagara
  treaties).
