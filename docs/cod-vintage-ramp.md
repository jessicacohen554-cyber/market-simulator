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
  operating dates. A scalar per-plant COD necessarily approximates a genuinely
  mixed-vintage plant (one old base + a small recent addition); the capacity
  weighting is the closest single date to the true per-unit online-capacity
  fraction. Measured on the ERCOT 2023 bins it removes ~870 MW of cap-month-
  equivalent phantom capacity, vs ~930 MW for the exact per-unit fraction and
  ~670 MW for an "earliest-unit" rule that under-drops recent-bulk plants.
* **Retirement** is recorded only when *every* unit of the plant carries a
  planned retirement (the whole plant goes away), using the latest such date, so
  capacity is kept until the last unit retires; a partial retirement leaves the
  plant online.
* Plants present only in the curated master registry (`year_built`, year-only)
  are back-filled at a mid-year default month (`COD_FALLBACK_MONTH = 7`).

### How each fleet path gets its COD

`cod_ramp.effective_cod` resolves each generator's date, **plant-code map first**:

* **ERCOT CAMPD bins** carry no build date of their own (the bins CSV has no
  build year), so the plant-code map is what gives them month precision — this
  was the path the duplicate implementation had to special-case.
* **Raw EIA-860 `Generator`s** (nuclear, oil, every non-ERCOT ISO) fall back to
  their own `online_year` / `online_month` when their plant is absent from the
  map; the model's `2000` default is treated as "vintage unknown" so a real
  pre-existing unit is never dropped.

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
