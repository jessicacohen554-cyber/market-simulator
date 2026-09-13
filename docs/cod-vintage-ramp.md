# Commercial-operation-date (COD) vintage ramp

*Single source of truth for "what was actually built" in a solved year.*

## Why

A backcast solves one historical year, but the dispatch fleet snapshot — the
curated ERCOT CAMPD bins and the EIA-860 generator parquet — is a *recent*
vintage. Left unfiltered it includes units commissioned **after** the solved
year, so a 2023 backcast dispatches capacity that did not yet exist, inflating
reserve headroom and suppressing the scarcity prices the LP can set. Renewables
and storage already ramp by their EIA-860 commercial-operation dates
(`vintage_capacity_ramp`, `storage_vintage_ramp`); this is the thermal / nuclear
/ oil analogue, so **every** generator obeys the same rule.

## The single mechanism

One monthly online mask, applied inside
`fleet.generators_to_fleet_arrays` and gated on `config.cod_ramp_enabled`
(default **on** for backcasts). For each generator and the solved calendar
`year`, a 12-month boolean mask marks the months the unit was commissioned and
not yet retired, and that mask multiplies the hourly `availability` (and the
must-run floor `min_gen`, so the LP lower bound cannot force a not-yet-built or
retired unit to run):

* `online_year > year` → not yet built (offline all year);
* `online_year == year` → online from `online_month` on — a September-COD unit
  is **absent in the August scarcity hours**, which a flat annual prorate gets
  wrong;
* `retirement_year < year` → already retired (offline all year);
* `retirement_year == year` → online through `retirement_month`.

The mask is applied **last**, after every outage / derate / withholding layer,
so nothing re-raises an offline month. It is month-precise, covers every fleet
path, handles retirements, and is pure capacity accounting (no fitting) — so it
is forecast-applicable as well as backcast-correct.

## The COD source: EIA-860, keyed by plant code

The commissioning date comes from EIA-860 — the authoritative inventory — **not**
from CAMPD (which carries emissions, not build dates). `cod_ramp.load_cod_map()`
reduces `eia860_generator_operable.parquet` (a month-precise `Operating Month` /
`Operating Year` and `Planned Retirement Month` / `Year` for ~every operable
generator) to a per-plant map:

```
{plant_code: (online_year, online_month, retirement_year, retirement_month)}
```

* **Online date** is the **capacity-weighted** mean of the plant's units'
  operating dates — and since SOCO-15 (owner card S12, 2026-09-13) this scalar
  is the **fallback only**, used where an LP unit has no record of its own. A
  scalar per-plant COD necessarily approximates a genuinely mixed-vintage plant
  (one old base + a recent addition): measured by calling the code, Vogtle
  (plant 649) reads `(2005, 5)`, so both 2023/2024 AP1000s were online all
  twelve months of 2023 (12.98 TWh of phantom nuclear), while greenfield Lowman
  (`(2023, 9)`) ramped correctly. The mean was the estimate; the units' own
  dates are the measured input, so the resolver now serves the **grain the LP
  unit actually has** (see "How each fleet path gets its COD" below). The
  historical ERCOT-2023 measurement that motivated the weighting (~870 MW of
  cap-month-equivalent phantom removed, vs ~930 for the exact per-unit fraction)
  is the fraction the bin path now computes exactly.
* **Retirement** is recorded only when *every* unit of the plant carries a
  planned retirement (the whole plant goes away), using the latest such date, so
  capacity is kept until the last unit retires; a partial retirement leaves the
  plant online.
* Plants present only in the curated master registry (`year_built`, year-only)
  are back-filled at a mid-year default month (`COD_FALLBACK_MONTH = 7`).

## Within-window plant exits (the snapshot's blind spot)

The ramp can only age out a unit **that is in the fleet snapshot**. The
committed operable vintage is a single recent release (EIA-860 2025 Early
Release), so a whole plant that ran through part of the backcast window and
retired *before* that vintage is absent from **every** modeled year — the ramp
has nothing to mask, and the surviving plants silently over-dispatch to cover
the hole. The textbook case is **Mystic Generating Station** (plant `1588`, a
~1.4 GW CC in NEISO's Boston/NEMA zone): it generated ~1.3 TWh in 2023, ran
Jan–May 2024, and retired June 2024 — but the 2025ER carries no Mystic CC at
all (the early release omits pre-survey retirees).

The fix mirrors how the **forecast** runner injects EIA-860 planned additions:
a **backcast-only** loader injects the within-window exits.

* `scripts/data/process_eia860.py --retired-window-from <final-vintage.zip ...>`
  reads the "Retired and Canceled" sheet of each **final** EIA-860 vintage
  (2023, 2024 — which *do* carry Mystic with its real June-2024 retirement),
  keeps whole-plant exits that retired in or after `RETIREMENT_WINDOW_START`
  (2023, the window start) and are **absent from the operable snapshot**, and
  writes `eia860_generator_retired_within_window.parquet` in the canonical
  fleet schema. The unit's **actual** retirement month/year is written into the
  `planned_retirement_*` columns and `status` is forced to `OP`, so both
  consumers treat it uniformly:
  * `cod_ramp.load_cod_map()` unions this parquet with the operable schedule
    before the per-plant reduction, so the COD map gains the exit's retirement
    date and the ramp ages it out by month.
  * `fleet.load_retired_within_window(iso)` builds the matching `Generator`
    objects (zones from eGRID geography, fuel/CHP class as usual). The backcast
    fleet build in `run_calibration.py` and the backcast branch of `runner.py`
    union them into the base fleet — gated on `config.mode == "backcast"`, the
    exact mirror of `load_planned_additions` (forecast). A forecast solves a
    forward year and must **not** carry an already-retired unit, so it never
    sees them.
* **Whole-plant exits only.** A plant still present in the operable snapshot
  (a *partial* retirement) keeps its surviving units there, and the plant-keyed
  COD map holds the whole plant online — so its retired units are deliberately
  left out rather than injected with a retirement the plant-level map cannot
  represent. This is the same plant-level limitation the retirement rule above
  already documents.

Net effect for NEISO: the modeled `CC_REGULAR` plant set now **differs by year**
(Mystic present in 2023 + Jan–May 2024, absent in 2025) instead of the identical
post-retirement set every year, and the surviving CCs no longer over-dispatch to
cover Mystic's missing ~1.3 TWh.

### How each fleet path gets its COD

`cod_ramp.generator_online_mask` is the single resolver
`generators_to_fleet_arrays` calls; it serves the unit's **own** EIA-860 date at
the grain the LP unit has (SOCO-15, owner card S12; rule 14 `[R-ACCURATE]` —
the unit's date is the measured input, the plant mean is the estimate; rule 25
`[R-ISO-SCOPE]` — one seam, the same construction on every fleet path):

* **Raw EIA-860 `Generator`s** (nuclear, oil, biomass, any unbinned thermal
  plant) keep their **own** `online_year` / `online_month` for the online date
  through `effective_cod(..., is_plant_level=False)` — the same preference the
  Homer City seam already gave a unit's own retirement, applied to the other end
  of its life. The loader bridges each unit's `Operating Month` from the same
  vintage directory's raw operable sheet (`eia860._operating_month_by_unit`),
  because the processed generators parquet carries the year only. The model's
  `2000` default is still "vintage unknown", so such a unit takes the plant map
  and a real pre-existing unit is never dropped.
* **CAMPD bins** — every registered keeper's thermal fleet, ERCOT's curated
  sheet and the six synthesized `fleet_to_bins` ISOs alike — have no unit date
  of their own (a tranche's `online_year` is the registry / COD-year estimate
  `bins_to_fleet` stamps). They take the **measured monthly online-capacity
  fraction** of their own constituents: `cod_ramp.load_unit_cod_map()` lists
  each `(plant_code, fuel_type)`'s operable units `(nameplate, online_year,
  online_month)` from the same sheet, classified with the loader's own
  `_map_fuel_type` so `(3, "gas_cc")` is exactly Barry's CC units and Barry's
  coal bin never sees Barry A3's 2023-11 COD; `bin_online_fraction` is the
  nameplate-weighted mean of the units' own masks (endpoints exact). A
  greenfield bin still steps `000000001111`; a brownfield bin takes the
  intermediate fraction (Barry CC 2023: `0.58` through October, `1.0` from
  November). The fraction scales the bin's `availability` and its `min_gen`.
  **Online half only**: the bin's retirement stays whatever `effective_cod`
  resolves (plant-collapsed, or an exit cohort's own under
  `partial_plant_exit_carry`) — rule 19 `[R-ONE-MECH]`.
* **The plant-collapsed map** remains the fallback wherever neither exists: a
  bin whose `(plant, fuel)` has no operable units in the sheet, a registry-only
  plant, a unit whose own year is unknown, and the clean-data seam
  (`MARKET_SIM_USE_CLEAN`), whose frozen fleet schema carries no month.

Repair evidence, blast radius at LP grain for all seven keepers, and the A/B:
`docs/handoffs/PRECOMMIT-soco-15-2026-09-13.md` / `FINDING-soco-15-2026-09-13.md`.

## Year-matched vintage option (`eia860_vintage_year`)

The COD ramp above filters a single recent snapshot (the committed **2025 Early
Release**, operating years through 2025) down to the solved year. A year-matched
**native vintage** — the EIA-860 annual release for the solved year itself —
removes the two residual approximations the ramp carries: the capacity-weighted-
mean COD smear of a genuinely mixed-vintage plant, and the absence of units that
were operable in the solved year but retired before the 2025 snapshot (those
sit in the snapshot's `retired_and_canceled` file, so the ramp cannot re-add
them).

`ScenarioConfig.eia860_vintage_year` (default `None`, backcast-only) opts in:
set it to a year with a committed `data/raw/eia-860/vintage_<year>/`
(2023, 2024 ship today) and every EIA-860 loader — fleet, COD map,
wind/solar/storage, dual-fuel/CHP — reads the native release instead.
Mechanically it is a process-global active directory
(`config.paths.set_eia860_vintage`, called once per year-solve in
`run_calibration.run_year` and `runner.run_year`); the three `@lru_cache`d
loaders (`fleet._chp_by_plant`, `fleet.dual_fuel_plant_groups`,
`cod_ramp.load_cod_map`) key on the resolved directory, so the switch can never
serve a stale-vintage map. `vintage_<year>/` holds only the loader-consumed
parquets (generators, generator/storage operable + proposed, wind/solar
operable, multifuel, plant, owner), regenerated from the committed annual zip by
`scripts/data/process_eia860.py --zip eia860<year>.zip --out-dir
data/raw/eia-860/vintage_<year>`.

**Measured effect is small — this is a correctness/provenance refinement, not a
scarcity driver.** The COD-ramped 2025ER fleet already reproduces the native
vintage's ERCOT installed capacity to within **+485 MW (0.36%) for 2023** and
**+567 MW (0.38%) for 2024**; only **~244 MW (11 units, 2023)** were operable
then but dropped from the 2025ER snapshot via retirement, and the batteries that
could inflate evening-peak ORDC reserves differ by **< 305 MW**. So the native
vintage validates the ramp and tidies the edges; it does not manufacture missing
scarcity (the price mechanism does — see docs/ordc-overlay.md). Because the
month mask vs the native operable set moves the COD-year units, this is a
**gated** change: recalibrate before re-cutting a keeper.

## Reconciliation note (2026-06-17)

This mechanism replaced two overlapping COD implementations that briefly
coexisted on `main`:

* **A** — `cod_ramp_enabled`, a *year*-granular ramp that pro-rated COD-year
  units by a flat half-year share and scaled the CAMPD bin DataFrame
  pre-aggregation (`ramp_bins`) plus the raw fleet (`ramp_fleet`), keyed off the
  master registry `year_built` + EIA-860 `operating_year`.
* **B** — `thermal_vintage_ramp`, a *month*-granular hourly mask inside
  `generators_to_fleet_arrays` with retirement handling, but reaching only
  generators that carried an EIA-860 month — which the dominant ERCOT CAMPD-bin
  path did not.

The unified mechanism keeps **B's month mask + retirement handling** and gives it
**A's coverage** by enriching every generator — bins included — from the
month-precise EIA-860 plant-code map. The single flag is `cod_ramp_enabled`
(default on, backcast; forecast runs pass an explicit calendar year). `ramp_bins`
/ `ramp_fleet` / `online_fraction` / `load_cod_year_map` and the
`thermal_vintage_ramp` flag are deleted. Because the month mask moves the
COD-year units versus A's flat annual prorate, this is a **gated** change:
re-calibrate before re-cutting a keeper (run125 → run126).
