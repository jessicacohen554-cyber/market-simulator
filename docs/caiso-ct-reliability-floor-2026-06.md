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

## Grounding in the literature (how other models / ISOs handle this)

A review of production-cost and capacity-expansion practice (PLEXOS/SERVM RMR,
CAISO LCR, ReEDS, GenX) frames this floor:

* **Local reliability commitment is real and recurring, not a fitted artifact.**
  CAISO sets Local Capacity Requirements by N-1/N-1-1 contingency criteria
  *evaluated at a 1-in-10 summer-peak load condition* (CAISO 2023 Local Capacity
  Technical Report). The rule is contingency/topology-based, but it **binds at
  extreme-heat peak load**, so local gas runs disproportionately on hot days —
  exactly the temperature hot-limb measured above. RA resources additionally
  carry a **must-offer obligation** and fill **flexible-RA** 3-hour net-load
  ramps, both of which commit peakers out of the energy merit order.
* **Temperature-keyed reliability/availability has direct model precedent.**
  NREL **ReEDS 2025** makes the hourly thermal forced-outage rate a function of
  zone surface air temperature (calibrated to PJM's 40% gas-CT ELCC derate);
  ReEDS 2018 derated thermal capacity 0.5%/°C on hot slices. So keying a
  reliability/availability quantity to temperature is established national-lab
  practice, not an ad-hoc tweak.
* **This floor is the peak-conditioned form.** The afternoon-evening window plus
  the TMAX hot-limb trigger together make the floor bind only at the hot,
  high-load peak (the 1-in-10 summer-peak condition), keyed to a weather driver
  — consistent with the literature's "transmission constraint binding at summer
  peak" representation, in the tractable form a zonal LP without nodal load
  pockets can carry.

### Scope: why CT_PEAKER (and not, as first considered, the whole CT+ST+CC fleet)

Local RA is fleet-fillable in principle (RMR skews to steam/CC, and CC/ST also
show temperature hot-limbs in the CAMPD data). But the floor is applied only
where it is both **faithful** and **needed**:

* **CC_REGULAR** is already *over*-dispatched in the model (the expected
  no-commitment-LP signature: real CCs carry start-up / min-load / min-run costs
  that keep them committed, which an energy-only single-pass LP over-uses). A
  floor would worsen it — so CC is left unfloored.
* **ST_GAS** is a near-retired CAISO fleet: measured generation collapses to
  ~0.14 / 0.11 TWh in 2024 / 2025 (vs 1.38 in 2023), and the model already
  *over*-runs it those years. A reliability floor would force phantom steam — its
  residual is a fleet-availability/retirement problem, not a missing floor — so
  ST_GAS is left unfloored.
* **CT_PEAKER** is the class that is genuinely *under*-run by the missing
  local-RA commitment, so it is the class the floor restores.

## Companion finding — CT_CHP EOR-cogen over-dispatch (diagnosed, deferred)

The other half of the CAISO gas-mix error is **CT_CHP over-dispatch** (model
~7.0 TWh vs ~3.5 measured). The CAISO CT_CHP fleet is dominated by **Kern-County
enhanced-oil-recovery steam cogens** (Sycamore, Kern River, Midway Sunset,
Fresno, Badger Creek, Bear Mountain): they burn gas primarily to make oil-field
injection **steam**, with electricity a byproduct. The shared CT_CHP offer-curve
multipliers (1.1 / 1.2 / 1.4 × base HR, set for compact chemical-host cogens)
price these EOR units as efficient baseload, so the LP runs them flat at ~88% CF
— against a measured ~13% CF (e.g. Kern River 1.35 model vs 0.20 TWh actual). On
a power-only basis (fuel charged to electricity after the steam credit) their
heat rate is ~1.8-2.0× the reported topping-cycle simple HR, so a power-only-HR
re-price is the physically correct treatment.

**This fix is deferred** because it cannot be applied in isolation. A power-only
re-price (committed ~1.75) was trialled and **reverted**: with the total CAISO
gas envelope already over-sized by the import / energy-balance over-generation
drift, cutting the cheap CT_CHP baseload does **not** lower total gas — it
reshuffles straight onto **CC_REGULAR** (CC jumped +5 TWh worse, from +2.9 to
+8.3 over), because CC is the next-cheapest dispatchable. The EOR re-price must
therefore land **after** the total-gas / import-drift fix (so the freed energy
leaves the system as imports rather than inflating CC), not before. This is the
key remaining root cause for the next CAISO session, and it is the same
mechanism that limits the CT_PEAKER floor's net effect (forcing peakers on in an
over-sized envelope partly exports the surplus rather than backing down CC).

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
