# Per-Plant CAMPD Dispatch (offer-curve based)

This document describes how the ERCOT thermal fleet is turned into LP
dispatch units, replacing the earlier equal-width heat-rate binning of
`aggregate_fleet()`.

> **One plant = one LP generator.** Despite the file name
> (`custom-bin-assignments.csv`) and the `Bin_Label` column, the model
> does **not** aggregate plants into shared "bins" for dispatch, and it
> never uses a bin-weighted heat rate. Every plant dispatches on its own
> measured `Plant_Avg_HR_MMBtu_MWh`. "Binning" is a legacy label retained
> only as a human-readable grouping. If you are reasoning about why a
> single plant over/under-runs, reason about *that plant's* heat rate,
> committed floor, and offer curve — not a bin.

## Overview

Bins are derived from EPA CAMPD gross generation for 2023-2024,
cross-referenced with eGRID net generation and EIA-860 plant
characteristics. Each row in `data/raw/reference/custom-bin-assignments.csv` is one
EIA plant and one operational bin in the LP — **every plant gets its
own discrete bin**, with a unique LP unit id keyed on its plant code.
The zone-and-bin-number grouping in the CSV (e.g. `H_CC1`, `N_CT2
(8-9)`) is retained only as a human-readable label; it does not collapse
multiple plants into a shared LP generator.

A single plant whose coal and gas-steam units coexist (e.g. W A Parish,
plant code 3470) appears as two rows — one per `Plant_Group` — and
therefore as two LP bins with the correct fuel type each.

Each plant's grid capacity is split into a small set of bid **tranches**
that together form a rising offer curve. **No tranche carries a `pmin`
floor** — a unit's minimum-load behaviour comes from the Committed
tranche bidding cheaply, not from a hard `pmin`.

| Tranche             | Meaning                                              | LP treatment                                                                 |
|---------------------|------------------------------------------------------|------------------------------------------------------------------------------|
| **Must Run (MR%)**  | CHP host steam. 0% for non-CHP.                      | Removed from LP capacity; generation + CO₂ added back in post-processing.     |
| **Committed (MC%)** | Minimum stable load once started.                    | Cheap block (`base_hr × offer["committed"]`, e.g. 0.92×); carries the start cost + min-run window and is the only screened tranche. |
| **Economic**        | Normal incremental dispatch as price rises.          | Rendered as an **N-slice rising heat-rate ramp** (`_econ_curve_steps`), not one flat block — see [Economic ramp](#economic-ramp-the-default-dispatch-shape). |
| **Peaking (PEAK%)** | Duct-firing / steep incremental cost.                | A **separate flat scarcity tranche above the econ ramp** for every group (CC included). It sits at `base_hr × peak_mult` (CC: the per-plant duct-burner multiplier, ~2.0–2.6×), so there is a price *discontinuity* between the top of the econ ramp (`econ_high`) and this block — the wall that keeps efficient CCs out of their top CF bins (see `docs/cc-high-cf-investigation.md`). |

The `Pct_*` shares sum to 100% per plant. The **committed share** is not a
coarse class assumption: for CC it is derived per-plant from each unit's
own CAMPD record (the P5 of its CF over its online hours — minimum stable
load) and applied when `config.cc_committed_per_plant` is set (the ERCOT
default), via `fleet.CC_REGULAR_COMMITTED_PCT_BY_PLANT`. The CSV
`Pct_Committed` column is only the fallback for plants without CAMPD
coverage.

Non-ERCOT ISOs have no curated bin CSV: `fleet_to_bins` synthesizes the
same per-plant frame from the EIA-860 fleet plus the CAMPD-derived
`data/raw/_processed-legacy/thermal_tranches_<ISO>.csv` (committed %, coal must-run %,
and — where the artifact carries `peaking_pct` (CAISO onward) — a measured
per-plant CC duct-firing share, applied via `fleet.thermal_tranche_peaking`
under `cc_peaking_per_plant` and superseding the offer curve's class-wide
`pct_peaking`). The resulting assignments are committed for review as
`data/raw/_processed-legacy/bin_assignments_<ISO>.csv`
(`scripts/export_iso_bin_assignments.py`), one row per
`(Plant_Code, Plant_Group)` with a source tag per derived quantity
(`campd` vs `class_default`; CHP must-run carries its floor provenance).
Under `chp_steam_following`, a cogen whose measured committed floor exceeds
its grid-facing share once the BTM host pull-out is removed (Elk Hills,
Marcus Hook) is clamped into the grid share — committed keeps its measured
level, the scarcity peak gives way — so the LP never carries more than the
grid-facing capacity.

## Plant groups

`Plant_Group` is the primary classifier (`config/plant_taxonomy.py`). The
seven dispatched groups and their model fuel type:

| Group        | Fuel type | Notes                                  |
|--------------|-----------|----------------------------------------|
| `CC_CHP`     | `gas_cc`  | Combined-cycle cogeneration            |
| `CC_REGULAR` | `gas_cc`  | Grid-serving combined cycle            |
| `CT_CHP`     | `gas_ct`  | Combustion-turbine cogeneration        |
| `CT_PEAKER`  | `gas_ct`  | Peaking combustion turbines            |
| `ST_GAS`     | `gas_st`  | Legacy natural-gas steam boilers       |
| `ST_CHP`     | `gas_st`  | Gas steam cogeneration                 |
| `COAL`       | `coal`    | Coal steam (taxonomy splits coal into ranks `COAL_LIGNITE`/`COAL_PRB`/`COAL_BIT`/`COAL_WC` for fuel pricing) |

`gas_st` is a dedicated fuel type for legacy gas steam boilers (W A
Parish, Cedar Bayou, Handley, ...); both `ST_GAS` and `ST_CHP` map to it. It pays the Henry Hub gas price and
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

`bins_to_fleet()` converts each plant into LP tranches. The capacity
split is:

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
take-or-pay), and a CC's minimum-load behaviour from its cheap Committed
block — not a hard `pmin`.

**Band heat rates come from the offer curve, not the CSV `HR_Mult_*`
columns, whenever a curve is configured (the ERCOT default).** With
`offer_curve_by_group[group]` set:

```
committed_hr = base_hr * offer["committed"]                      # e.g. 0.92×
econ ramp    = base_hr * mult(t),  mult: econ_low → econ_high     # N-slice ramp
peak (CC)    = base_hr * cc_duct_burner_peak_mult(turbine_class)  # 2.0–2.5×, separate flat tranche above the ramp
```

Only when **no** offer curve covers the group do the CSV `HR_Mult_<tranche>`
columns (`hr_mc = Plant_Avg_HR × HR_Mult_Committed`, etc.) set the band
heat rates. Under the ERCOT calibration they are dormant — do not read the
CSV `HR_Mult_*` values as the dispatched band heat rates.

Emission rates are derived directly from the plant's **physical** heat rate
(`base_hr` = `Plant_Avg_HR`), **not** the bid-tranche heat rate:
`emission_rate = base_hr * FUEL_CO2_FACTOR_PER_MMBTU[fuel]`, uniform across a
plant's tranches. The offer-curve `HR_Mult_*` pricing multipliers (peak
×2.0–2.5, committed ×0.92) shape the bid stack only — a plant's CO2/MWh does
not change because a block is offered at a scarcity price (R2/EM-4). Where a
CEMS plant rate (or the forward v2 estimator) covers the plant, it overrides
this default per `model-methodology-spec.md` §Fleet.

Plants whose `Plant_Avg_HR_MMBtu_MWh` is blank in the CSV (a handful of
tiny unmetered CTs in CT_unassigned) fall back to a per-group default
heat rate before the tranche multipliers are applied.

## Economic ramp (the default dispatch shape)

This is how a CC/coal plant actually bids under the ERCOT calibration —
**not** an optional add-on. Above its cheap Committed block, the plant's
economic capacity (`econ_cap`, spanning econ-low → econ-high; the duct-firing
peak band is **not** folded in — it is a separate flat tranche above the ramp)
is sliced by `_econ_curve_steps` into `config.offer_curve_smoothing_n`
equal-capacity steps whose heat-rate multiplier rises:

```
mult(t) = lo + (pk − lo) * t**exp        t = (k + 0.5) / n,  k = 0 … n−1
```

with the active ERCOT values:

- `n   = config.offer_curve_smoothing_n`   (default **6**)
- `exp = config.offer_curve_smoothing_exp` (default **1.0** → a straight,
  linear ramp; `exp > 1` would be convex / cheap-bottomed)
- `lo  = offer_curve_by_group[group]["econ_low"]`  (CC_REGULAR ≈ **1.06**)
- `pk  = econ_high` — the **top of the econ ramp**, not the duct-firing
  multiplier. The duct-firing peak (`cc_duct_burner_peak_mult(turbine_class)` for CC —
  F-class **2.25**, G/H-class **2.50**, older **2.00** — or
  `offer_curve_by_group[...]["peak"]`) is a **separate flat tranche above the
  ramp**, so there is a deliberate price jump from `econ_high` to the peak
  block.

So each CC plant is a Committed block at `base_hr × ~0.9` followed by N rising
econ slices from `base_hr × econ_low` up to `base_hr × econ_high`, then a flat
duct-firing block at `base_hr × ~2.0–2.5`, scaled entirely by **its own**
`base_hr`. The plant fills slice by slice as the hourly price clears each step;
the top flat block only clears in scarcity hours, which is what keeps efficient
CCs from reaching their observed >90 % CF mass (see
`docs/cc-high-cf-investigation.md`).

The econ ramp spans **econ-low → econ-high for every group**; the peak band is
always a separate flat scarcity tranche above it. (`_CURVE_FOLD_PEAK` — which
once folded the CC/coal duct-firing band into the ramp top — has been removed;
`fleet.py` now reads "Nothing is folded into the ramp.")

**Why a plant over/under-runs is set here.** The over/under of a single CC
versus CAMPD is driven by (1) its `base_hr` anchor (it scales every slice)
and (2) its per-plant committed share — both plant-specific — measured
against ERCOT's real, partly non-economic commitment. Because the ramp
anchors on annual-average `base_hr` and starts at `econ_low ≈ 1.06`, a
flexible cycler whose true full-load incremental heat rate is better than
its annual average (e.g. Jack County) has its economic slices priced too
high and under-runs; the lever is `econ_low` / the ramp slope / the
`base_hr` definition, not the bin structure.

## Per-plant tranche-config override sheet (5-slice rising offer curve)

The default above sets each plant's split and band heat rates from
per-*group* values (`offer_curve_by_group`) and the per-plant
committed/peaking dicts. For calibration we sometimes need to shape an
**individual** plant's offer curve without disturbing its class — so a
plant can be steered to match its own observed CF behaviour while the class
total stays on target. That is the job of the optional per-plant
tranche-config sheet (`data/raw/reference/plant-tranche-config.csv`, pointed at by
`ScenarioConfig.plant_tranche_config_path`; **off by default**).

The sheet refines the four tranches into a **five-slice rising offer
curve** by splitting Economic into a low and a high band, so each plant
offers progressively pricier blocks as output climbs:

| Slice | Share column | HR-multiplier column |
|-------|--------------|----------------------|
| Must-Run  | `Pct_Must_Run`  | `HR_Mult_Must_Run`  (VOM-only bid; fuel sunk) |
| Committed | `Pct_Committed` | `HR_Mult_Committed` |
| Econ-Low  | `Pct_Econ_Low`  | `HR_Mult_Econ_Low`  |
| Econ-High | `Pct_Econ_High` | `HR_Mult_Econ_High` |
| Peaking   | `Pct_Peaking`   | `HR_Mult_Peaking`   |

The five `Pct_*` are shares of nameplate (sum to 100); the five
`HR_Mult_*` multiply the plant's base HR for the block priced in that
slice (e.g. `1.00 → 1.00 → 1.01 → 1.22 → 1.95` for an F-class CHP CC). The
remaining sheet columns (name, group, config, turbine class, zone) are
reference-only and ignored by the loader.

**Smooth N-slice rendering.** The five `Pct_*`/`HR_Mult_*` rows are the
*configuration*; in the LP the economic region is rendered by the same
`_econ_curve_steps` ramp described under
[Economic ramp](#economic-ramp-the-default-dispatch-shape) —
`config.offer_curve_smoothing_n` steps (default 6) of
`mult(t) = lo + (pk − lo) × t**exp` with `exp = config.offer_curve_smoothing_exp`
(default 1.0, linear) — so the unit fills gradually as the hourly price
crosses its rising MC instead of parking at the top of a flat block. For
**every group** the curve spans only econ-low → econ-high and the peak band
stays a separate flat **scarcity** tranche above it (its high multiplier is a
price-wall floor, not a real ramp endpoint). This is true for CC/coal as well
as CT/ST: the earlier "fold the peak into the CC ramp" behaviour was removed,
so a CC has a deliberate price discontinuity between `econ_high` and its
duct-firing block (the cause of the missing >90 % CF hours — see
`docs/cc-high-cf-investigation.md`).

`fleet.load_plant_tranche_config()` reads the sheet,
`_bands_from_shares()` converts the cumulative shares into capacity-factor
band edges, and `plant_tranche_bands()` builds the per-plant offer curve
used by both the LP and the dashboard's tranche markers. **When a plant is
listed in the sheet, its split and band heat rates come straight from the
sheet, bypassing `offer_curve_by_group` and the per-plant committed/peaking
dicts**; plants absent from the sheet keep the configured group defaults.
The sheet is produced and round-tripped by
`scripts/export_tranche_config.py` and edited via the desktop launcher
(`tools/launcher.py`).

A related opt-in, `cc_peaking_per_plant` (default `False`), overrides where
the duct-burner peak band starts on the CF axis for the CC_REGULAR plants
in `fleet.CC_REGULAR_PEAKING_PCT_BY_PLANT` — moving the expensive peak
slice earlier (e.g. 15% ⇒ peaking starts at 85% of nameplate) for the four
F-class(late) 2×1 CCs the model otherwise over-runs in the 80–90% CF band;
the economic tranche absorbs the difference. Other CC_REGULAR plants keep
the offer-curve value.

## Fuel pricing

`market_sim.data.fuel.resolve_fuel_prices` prices fuel differently for gas
and coal.

**Gas — uniform price.** Every gas generator in the ISO pays the *same*
delivered price for a year: the AEO Henry Hub trajectory plus the ISO basis
differential, optionally seasonally shaped. Per-plant gas costs are **off
by default** (`ScenarioConfig.gas_plant_monthly_fuel_pricing`). EIA-923
Schedule-5 gas reporting is sparse — only ~12% of ERCOT CC capacity reports
a delivered cost — and merchant CCs in a hub all buy gas in the same
market, so giving the few reporting plants their own (often higher,
winter-spiking) cost while suppressed peers pay the smoothed trajectory
created a spurious intra-zone price asymmetry (it penalised Jack County
against its North-zone neighbours). Set the flag `True` to restore
per-plant gas costs where EIA-923 reports them.

**Coal — per-plant where reported.** Coal carries genuinely distinct
delivered costs (lignite mine-mouth vs railed PRB), so each coal plant that
reports EIA-923 monthly receipts pays its own measured monthly delivered
cost (`coal_plant_monthly_pricing`, on by default), broadcast to the hourly
horizon; months with no reported cost, and plants outside the sample, fall
back to the per-year coal supply-class trajectory.
`scripts/process_f923_fuel_costs.py` builds
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`.

The same resolver runs both backcasts and forward projections; in a forward
year the F923 lookup finds nothing and every plant falls through to the
trajectory-based default.

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
- Tranche profiles by group — **legacy/fallback shares only.** These are
  the coarse CSV `Pct_*` defaults; under the ERCOT calibration the CC
  committed and peaking shares are replaced per-plant from CAMPD
  (`cc_committed_per_plant` / `cc_peaking_per_plant`), so do not read this
  table as the dispatched split for a given CC plant:

  | Group       | MR% | MC%   | ECON% | PEAK% | Min run | Min down |
  |-------------|-----|-------|-------|-------|---------|----------|
  | CC_CHP      | 60  | 15    | 15    | 10    | 24h     | 4h       |
  | CC_REGULAR  | 0   | 48-50 | 30-35 | 15-20 | 10-12h  | 4-6h     |
  | COAL        | 0   | 40    | 45    | 15    | 36h     | 16h      |
  | CT_CHP      | 62-65 | 15-17 | 15-16 | 5-6 | 23h     | 2h       |
  | CT_PEAKER   | 0   | 30-40 | 25-27 | 25-45 | 1h     | 1h       |
  | ST_GAS      | 0   | 20    | 40    | 40    | 4h      | 4h       |

## CHP must-run post-processing

The must-run tranche of a CHP bin is removed from the LP because its
generation is fixed by a steam contract, not by market economics. After
dispatch, `compute_must_run_emissions()` reconstructs that generation and
its CO2 for asset-level emissions trajectories:

```
# Primary path — when metered generation is supplied:
mr_gen_mwh  = max(0, total_gen_by_plant - grid_gen_by_plant)   # behind-the-meter portion
mr_mw       = mr_gen_mwh / 8760

# Fallback — only when no metered total is available:
mr_mw       = nameplate * MR% / 100
mr_gen_mwh  = mr_mw * 8760 * must_run_cf                        # must_run_cf default 0.85

mr_co2_tons = mr_gen_mwh * emission_rate
```

This applies to both `CC_CHP` and `CT_CHP` (non-coal must-run plants).

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
| Single coal trajectory for every coal plant | Per-plant monthly EIA-923 delivered cost for reporting coal plants (gas stays uniform AEO Henry Hub by default) |

The legacy path is still available via `use_campd_bins=False`, which
restores `aggregate_fleet()` and the take-or-pay coal tranches.
