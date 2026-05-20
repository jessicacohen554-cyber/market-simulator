# CAMPD-Based Binning + 4-Tranche Dispatch

This document describes how the ERCOT thermal fleet is binned into
operational dispatch units, replacing the earlier equal-width heat-rate
binning of `aggregate_fleet()`.

## Overview

Bins are derived from EPA CAMPD gross generation for 2023-2024,
cross-referenced with eGRID net generation and EIA-860 plant
characteristics. Each row in `inputs/custom-bin-assignments.csv` is one
EIA plant and one operational bin in the LP — **every plant gets its
own discrete bin**, with a unique LP unit id keyed on its plant code.
The zone-and-bin-number grouping in the CSV (e.g. `H_CC1`, `N_CT2
(8-9)`) is retained only as a human-readable label; it does not collapse
multiple plants into a shared LP generator.

A single plant whose coal and gas-steam units coexist (e.g. W A Parish,
plant code 3470) appears as two rows — one per `Plant_Group` — and
therefore as two LP bins with the correct fuel type each.

Each bin carries a **4-tranche capacity structure** that maps directly to
LP dispatch behavior:

| Tranche             | Meaning                                              | LP treatment                                                    |
|---------------------|------------------------------------------------------|-----------------------------------------------------------------|
| **Must Run (MR%)**  | Always dispatched (CHP steam). 0% for non-CHP.       | Removed from LP capacity; added back in post-processing.        |
| **Committed (MC%)** | Minimum stable load once started.                    | Sets `pmin` on the base generator.                              |
| **Economic (ECON%)**| Normal dispatch when price clears marginal cost.     | Standard LP dispatch range between `pmin` and the base ceiling. |
| **Peaking (PEAK%)** | Duct-firing / steep incremental cost.                | A separate `_peak` generator with a heat-rate penalty.          |

Tranche percentages sum to 100% per bin.

## Plant groups

`Plant_Group` is the primary classifier. The six dispatched groups and
their model fuel type:

| Group        | Fuel type | Notes                                  |
|--------------|-----------|----------------------------------------|
| `CC_CHP`     | `gas_cc`  | Combined-cycle cogeneration            |
| `CC_REGULAR` | `gas_cc`  | Grid-serving combined cycle            |
| `CT_CHP`     | `gas_ct`  | Combustion-turbine cogeneration        |
| `CT_PEAKER`  | `gas_ct`  | Peaking combustion turbines            |
| `GAS_STEAM`  | `gas_st`  | Legacy natural-gas steam boilers       |
| `COAL`       | `coal`    | Coal steam                             |

`gas_st` is a dedicated fuel type for legacy gas steam boilers (W A
Parish, Cedar Bayou, Handley, ...). It pays the Henry Hub gas price and
carries its own VOM, NOx and forced-outage parameters. Plants in the
registry's `OTHER` group are non-dispatchable (BTM-only, industrial, or
too small) and never enter the LP.

## Binning rules

1. **Per zone, per resource type.** Bins never span zones. A bin's heat
   rate is the capacity-weighted average of its plants within the zone.
2. **Small groups (< 10 plants per resource-zone): one plant per bin.**
   This gives plant-level resolution for combined cycles, coal and CT
   cogeneration where there are few plants per zone.
3. **Large groups (>= 10 plants per resource-zone): bin by HR + CF.**
   Plants are grouped when they have close heat rates *and* close annual
   capacity factors. This mainly applies to `CT_PEAKER`.
4. **Small-plant exception.** Plants < 100 MW do not create a new bin
   solely because they differ; they join the nearest bin unless doing so
   would push the bin's heat-rate range past 2 MMBtu/MWh.
5. **Heat-rate range ceiling: 2 MMBtu/MWh per bin.**
6. **Extreme outliers always get their own bin** even if < 100 MW.

## From bins to LP generators

`load_campd_bins()` normalises the per-plant detail CSV into the
one-bin-per-plant LP schema: one DataFrame row per CSV row, with a
`Plant_Code`, the plant's own `Plant_Avg_HR_MMBtu_MWh`, and four
tranche heat rates derived from the CSV's `HR_Mult_<tranche>` columns:

```
hr_mr   = Plant_Avg_HR × HR_Mult_Must_Run
hr_mc   = Plant_Avg_HR × HR_Mult_Committed
hr_econ = Plant_Avg_HR × HR_Mult_Economic
hr_peak = Plant_Avg_HR × HR_Mult_Peaking
```

A blank `HR_Mult_<tranche>` cell (for a tranche that has zero capacity
on that plant) inherits a per-group default so the arithmetic is
well-defined even if a sensitivity run later activates that tranche.

`bins_to_fleet()` converts each plant into up to four LP tranches
keyed to the CSV percentages and per-tranche heat rates:

```
mustrun_cap   = nameplate * MR% / 100            # coal only — sunk fuel
grid_cap      = nameplate - mustrun_cap          # for coal
                nameplate * (1 - MR% / 100)       # for non-coal (steam
                                                  # cogen off-grid)
committed_cap = grid_cap * MC%   / (100 - MR%)
peak_cap      = grid_cap * PEAK% / (100 - MR%)
econ_cap      = grid_cap - committed_cap - peak_cap
```

Every tranche carries `pmin_mw = 0`; coal's baseload behavior emerges
from the mustrun tranche bidding at VOM only (its fuel is sunk under
take-or-pay).

Emission rates are derived directly from the heat rate:
`emission_rate = heat_rate * FUEL_CO2_FACTOR_PER_MMBTU[fuel]`.

Plants whose `Plant_Avg_HR_MMBtu_MWh` is blank in the CSV (a handful of
tiny unmetered CTs in CT_unassigned) fall back to a per-group default
heat rate before the tranche multipliers are applied.

## Per-plant fuel pricing

Each tranche carries its plant code, which routes a per-plant monthly
delivered fuel cost from EIA-923 Schedule 5 into the LP marginal cost.
`scripts/process_f923_fuel_costs.py` processes the F923 zips into
`inputs/processed/eia923_monthly_fuel_costs.parquet`, and
`market_sim.data.fuel.resolve_fuel_prices` applies one of two paths to
each gas / coal generator:

1. **Historical years (F923 available)** — the generator pays its plant's
   own measured monthly delivered cost, broadcast to the hourly
   horizon. Months with no reported cost (EIA suppression) keep the
   per-fuel default.
2. **Forward years (or plants outside the F923 sample)** — gas units
   pay the AEO Henry Hub trajectory plus the ISO basis differential;
   coal units pay the per-year coal trajectory. An entire plant class
   / zone shares the same forward price, per the project's stated
   model design.

The same resolver runs both backcasts and forward projections; the
F923 lookup simply finds nothing in a forward year and every plant
falls through to the trajectory-based default.

## Commitment

Commitment parameters (`min_run_hours`, `min_down_hours`,
`startup_cost_per_mw`) come straight from the bin — no lookup tables.

- **Coal** is commitment-screened in pass 2 alongside CC/CT. Its 36-hour
  minimum run and high startup cost ($100/MW) keep it on through all but
  the longest low-price spells, but it can decommit. When committed it
  dispatches at its 40% committed floor and ramps with economics.
- **Peak generators** carry `min_run_hours = 0` and stay out of the
  screen; only the base generator is screened.
- The legacy (`use_campd_bins=False`) fleet keeps the old behavior: its
  take-or-pay coal is never screened and is pinned to the P1 dispatch.
- Tranche profiles by group (representative values):

  | Group       | MR% | MC%   | ECON% | PEAK% | Min run | Min down |
  |-------------|-----|-------|-------|-------|---------|----------|
  | CC_CHP      | 60  | 15    | 15    | 10    | 24h     | 4h       |
  | CC_REGULAR  | 0   | 48-50 | 30-35 | 15-20 | 10-12h  | 4-6h     |
  | COAL        | 0   | 40    | 45    | 15    | 36h     | 16h      |
  | CT_CHP      | 62-65 | 15-17 | 15-16 | 5-6 | 23h     | 2h       |
  | CT_PEAKER   | 0   | 30-40 | 25-27 | 25-45 | 1h     | 1h       |
  | GAS_STEAM   | 0   | 20    | 40    | 40    | 4h      | 4h       |

## CHP must-run post-processing

The must-run tranche of a CHP bin is removed from the LP because its
generation is fixed by a steam contract, not by market economics. After
dispatch, `compute_must_run_emissions()` reconstructs that generation and
its CO2 for asset-level emissions trajectories:

```
mr_mw       = nameplate * MR% / 100
mr_gen_mwh  = mr_mw * 8760 * must_run_cf      # must_run_cf default 0.85
mr_co2_tons = mr_gen_mwh * emission_rate
```

This applies to both `CC_CHP` and `CT_CHP`.

## What this replaces

| Old                                                    | New                                                                              |
|--------------------------------------------------------|----------------------------------------------------------------------------------|
| `aggregate_fleet(n_bins=...)`                          | `load_campd_bins()` → one LP bin per EIA plant                                   |
| Equal-width heat-rate binning                          | Per-plant Plant_Avg_HR with HR_Mult tranche multipliers                          |
| Multi-plant aggregated bins (~129 LP bins)             | ~302 LP bins, one per plant (W A Parish coal + gas-steam = 2 bins)               |
| Bin-weighted heat rate                                 | Plant-specific Plant_Avg_HR × CSV HR_Mult per tranche                            |
| Uniform CHP grid derate                                | Per-plant MR% from the CSV                                                       |
| Uniform CC min-gen fraction                            | Per-plant MC% from the CSV                                                       |
| CC max-CF cap                                          | Per-plant ECON + PEAK split                                                      |
| Coal take-or-pay supply curve                          | Coal 40% MC / 45% ECON / 15% PEAK per plant in the bins                          |
| `CC/CT_COMMITMENT_PARAMS` tables                       | Per-plant `min_run` / `min_down` from the CSV                                    |
| Single AEO Henry Hub gas price for every gas generator | Per-plant monthly EIA-923 delivered cost (historical), AEO trajectory (forward)  |

The legacy path is still available via `use_campd_bins=False`, which
restores `aggregate_fleet()` and the take-or-pay coal tranches.
