# CAISO CT_PEAKER local-RA reliability floor (temperature-driven)

*2026-06 — companion to `docs/ercot-st-gas-netload-drag-2026-06.md`.*

## The miss

Against the fold-in classFull benchmark the CAISO backcast carried a persistent,
same-sign **gas merit-split** error every year:

| class        | model (2023) | actual (2023) | error |
|--------------|-------------:|--------------:|------:|
| CC_REGULAR   | ~58.1 TWh    | ~54-55 TWh    | **over +3.2** |
| CT_PEAKER    | ~0.15 TWh    | ~4.4-5.1 TWh  | **under -4.2** |

Total gas was in band — only the **mix** was wrong: the energy that should run
on the simple-cycle peakers instead spilled onto the cheaper combined-cycle
fleet. An energy-only LP will never do otherwise: CT_PEAKER sits at the top of
the merit order, so on pure energy economics it is the *last* thing dispatched,
yet CAISO runs its peakers 4-5 TWh/yr.

## Why CAISO runs peakers off the energy merit order

CAISO commits its simple-cycle gas peakers for **local Resource Adequacy**, not
system energy. The local capacity areas (LA Basin, Big-Creek-Ventura, Bay-Area)
have transmission-import limits that bind hardest on hot afternoons, when the
load-pocket cooling load climbs and rooftop+utility solar collapses into the
sunset net-load ramp. RA-obligated fast-start CTs in those pockets are committed
through that afternoon-evening ramp for local reliability **regardless of whether
they are in the money on system energy**. This is a real, recurring,
weather-driven operating rule — and an energy-only LP has no representation of
it, hence the under-run.

## The trigger is temperature (a clean monotonic hot-limb)

Mirroring the ERCOT gas-steam derivation, we regressed the **measured** CAISO
CT_PEAKER operating level on candidate in-model triggers. Unlike ERCOT's
overnight steam (bimodal in temperature, so net-load was the better unifier),
CAISO CT operation is a **summer-heat peaker** signal with a clean **monotonic
hot limb** in temperature:

* Measured CT_PEAKER fleet: EPA CAMPD simple-cycle combustion-turbine units in
  California, 2023-2025 (hourly gross load).
* Weather: NOAA GHCN-Daily TMAX for seven CAISO load-center metros (LA, Burbank,
  San Diego, Fresno, Sacramento, San Jose, San Francisco), load-weighted into a
  single CAISO daily max temperature. Archived to
  `data/raw/caiso-weather/caiso_load_weighted_tmax_daily.csv` so it regenerates
  from a forward weather year exactly as the load / wind / solar shapes do.

Evening (15-22 local) CT fleet capacity factor by daily TMAX bin (median):

| TMAX (°C) | ≤24 | 26 | 28 | 30 | 32 | 34 | 36 |
|---|---|---|---|---|---|---|---|
| evening CF | ~0.04 | 0.05 | 0.10 | 0.24 | 0.36 | 0.43 | 0.51 |

Below ~25-26 °C the fleet sits flat on a small price/baseline level; above it CT
rises sharply and **monotonically** with temperature — the heat-driven local-RA
commitment. The hot-day (TMAX ≥ 30 °C) hourly shape peaks 16-19 local and the
15-22 window carries ~80% of hot-day CT energy (the duck-curve neck).

### Pooled fit

Least-squares line on the hot limb (TMAX ≥ 26 °C, 2023-2025 pooled), evening
window:

```
floor_frac = clip(0.047 · (TMAX_degC − 25), 0, 0.46)
```

These are the `ScenarioConfig` defaults `caiso_ct_floor_slope_per_c` /
`caiso_ct_floor_t0_c` / `caiso_ct_floor_cap`. The cap (0.46) is the p97 of the
measured evening CF — the hottest-day local-RA ceiling, so the line never
extrapolates past the observed envelope.

This is a measured **temperature → commitment** rule, **not** a fit to a
generation/TWh residual: the curve is fixed by the weather-vs-CF regression, and
whatever annual CT energy it produces is what it produces. It deliberately
floors only the **heat-driven** commitment; the small all-temperature evening
baseline (~5% CF, the year-round local-RA minimum that is *not* weather-driven)
is left to the economic dispatch, not forced.

## Why temperature, not net-load (CLAUDE.md #10/#11)

* **Forward-derivable.** A forecast year already pins a weather year (it has a
  load forecast, a wind/solar build, and a temperature year). The same NOAA TMAX
  series threads into a forward run with no new fitted input.
* **Condition-responsive.** Hotter years / a warming climate raise TMAX and so
  the floor; the mechanism scales with the physical driver, not a calendar.
* **Not a CEMS pin.** The floor is a smooth `frac(TMAX)` rule applied to *current*
  available CT capacity, distributed cheapest-first — it never pins a unit to its
  observed hourly output (the rejected `ct_deployment_overlay` pattern, PR #888).
* **Weather, not just load.** Per review guidance, the reliability commitment is
  justified by a temperature variable that physically explains keeping the units
  online (heat → load-pocket cooling load → local import limits bind), not by a
  bare net-load floor.

## Mechanism (code)

* `ScenarioConfig.caiso_ct_reliability_floor` (default **off**; `_calibration_
  config` defaults it **on** for CAISO, off for every other ISO) enables the
  floor; the curve coefficients are `caiso_ct_floor_slope_per_c` (0.047),
  `caiso_ct_floor_t0_c` (25.0), `caiso_ct_floor_cap` (0.46).
* `data.eia_loader.caiso_load_weighted_tmax` reads the archived daily TMAX and
  broadcasts it to the run hours.
* `model.transmission.inject_caiso_ct_reliability_floor` floors the CT_PEAKER
  rows at `clip(slope·(TMAX−T0), 0, cap) × available capacity` over the
  afternoon-evening window (`CAISO_CT_FLOOR_HOURS = (15, 22)`), via the
  hour-varying `FleetArrays.min_gen` lower bound (cheapest-first, composed with
  any existing floor via `maximum`). The LP dispatches economically above it, so
  it only binds on the hot-day evening hours an energy-only merit order leaves
  the peakers off.
* CLI: `--caiso-ct-reliability-floor` / `--no-caiso-ct-reliability-floor`
  (tri-state; unset keeps the per-ISO base default).
* Re-derive: `python scripts/derive_caiso_ct_reliability_floor.py`
  (`--no-fetch` to re-regress from the archived TMAX).
