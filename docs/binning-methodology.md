# CAMPD-Based Binning + 4-Tranche Dispatch

This document describes how the ERCOT thermal fleet is binned into
operational dispatch units, replacing the earlier equal-width heat-rate
binning of `aggregate_fleet()`.

## Overview

Bins are derived from EPA CAMPD gross generation for 2023-2024,
cross-referenced with eGRID net generation and EIA-860 plant
characteristics. Each plant in `inputs/custom-bin-assignments.csv` is
assigned to one operational bin. Bins never span zones or plant groups.

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

`load_campd_bins()` aggregates the per-plant detail CSV to one row per
unique bin, keyed by `(Plant_Group, ERCOT_Zone, Bin_Number, Bin_Label)`.
`Bin_Label` alone is not unique — labels such as `S_CC1` or `CT1 (8-9)`
recur across zones — so the full composite key identifies a bin.

`bins_to_fleet()` converts each bin into 1-2 LP generators:

```
grid_cap = nameplate * (1 - MR% / 100)        # must-run removed
peak_frac = PEAK% / (100 - MR%)
base_cap  = grid_cap * (1 - peak_frac)
peak_cap  = grid_cap * peak_frac
pmin      = grid_cap * MC% / (100 - MR%)      # base generator floor
```

- **Base generator** (`{bin}_base`): capacity `base_cap`, `pmin` from the
  committed tranche, the bin's weighted heat rate.
- **Peak generator** (`{bin}_peak`, only when `peak_cap > 0.5 MW`):
  capacity `peak_cap`, `pmin = 0`, heat rate scaled by a duct-firing
  penalty (`cc_peak_hr_penalty` 1.15, `ct_peak_hr_penalty` 1.10,
  `coal_peak_hr_penalty` 1.08), and 1.5x VOM for peaking operation.

Emission rates are derived directly from the heat rate:
`emission_rate = heat_rate * FUEL_CO2_FACTOR_PER_MMBTU[fuel]`.

Bins whose `Bin_Zone_Weighted_Avg_HR` is blank in the CSV (a handful of
tiny unmetered CTs and two combined cycles) fall back to the mean
plant-level heat rate, then to a per-group default.

## Commitment

Commitment parameters (`min_run_hours`, `min_down_hours`,
`startup_cost_per_mw`) come straight from the bin — no lookup tables.

- **Coal** is never commitment-screened: its 36-hour minimum run confirms
  ERCOT coal does not decommit in practice. It dispatches at its 40%
  committed floor and ramps with economics.
- **Peak generators** carry `min_run_hours = 0` and stay out of the
  screen; only the base generator is screened.
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

| Old                              | New                                            |
|----------------------------------|-------------------------------------------------|
| `aggregate_fleet(n_bins=...)`     | `load_campd_bins()` -> bins from CSV            |
| Equal-width heat-rate binning     | CAMPD-derived bins by HR + CF + zone            |
| Uniform CHP grid derate           | Per-bin MR% from the CSV                        |
| Uniform CC min-gen fraction       | Per-bin MC% from the CSV                        |
| CC max-CF cap                     | Per-bin ECON + PEAK split                       |
| Coal take-or-pay supply curve     | Coal 40% MC / 45% ECON / 15% PEAK in the bins   |
| `CC/CT_COMMITMENT_PARAMS` tables  | Per-bin `min_run` / `min_down` from the CSV     |

The legacy path is still available via `use_campd_bins=False`, which
restores `aggregate_fleet()` and the take-or-pay coal tranches.
