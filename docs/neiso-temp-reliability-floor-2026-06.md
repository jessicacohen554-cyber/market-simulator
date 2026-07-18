# NEISO weather-correlated reliability floor (dual-limb, temperature-driven)

## The miss

An energy-only LP under-runs two structurally distinct ISO-NE fleets and spills
their energy onto the cheaper combined-cycle stack:

- **CT_PEAKER** (37 plants, ~1.2 GW nameplate) — simple-cycle gas peakers the
  model leaves near-idle because they sit at the top of the merit order.
- **COAL** (the lone Merrimack-class unit, ~108 MW) and **ST_GAS** (a lone
  steam-gas unit, ~81 MW) — cold-snap reliability units the energy-only merit
  order almost never dispatches.

## The trigger is temperature — but on **opposite limbs**

Unlike CAISO/NYISO, where the peaker miss is a summer-only cooling phenomenon,
ISO-NE is a **dual-limb** weather system. Regressing the measured CAMPD capacity
factor (pooled 2023-2025) on the NEISO load-weighted daily temperature
(`scripts/data/derive_neiso_temp_reliability_floor.py`, NOAA GHCN-Daily TMAX/TMIN over
Boston Logan, Providence, Hartford-Bradley, Portland-ME, Concord-NH,
Burlington-VT) separates the fleets cleanly:

| Class      | Limb            | Window           | Spearman ρ | Driver |
|------------|-----------------|------------------|-----------|--------|
| CT_PEAKER  | hot (TMAX)      | HB16-21          | +0.47     | summer cooling ramp |
| COAL       | cold (TMIN)     | HB6-9 + HB17-20  | +0.35     | winter gas-electric constraint |
| ST_GAS     | cold (TMIN)     | HB6-9 + HB17-20  | +0.40     | winter gas-electric constraint |

CT_PEAKER tracks the summer **hot limb** (CF rises with TMAX, ~0 correlation
with cold). COAL and ST_GAS track the winter **cold limb** (CF rises as TMIN
falls, ~0 correlation with heat): in a deep cold snap the New England gas
pipeline is bid away by heating load, gas-electric basis blows out, and these
oil/coal/steam units price into merit for local reliability. This is exactly the
behaviour the request flagged — "steam gas and coal bituminous run around the
same times each year, during cold snaps."

### Pooled fit (CF normalized by bin nameplate = the model's pmax basis, clipped [0,1])

**Hot limb — CT_PEAKER, evening HB16-21, T0 = 25 °C**

```
neiso_ct_floor_slope_per_c = 0.0374   (hot-limb, TMAX >= T0)
neiso_ct_floor_cap         = 0.479    (p97 evening CF)
neiso_ct_floor_base        = 0.000    (cool-day evening p25)
```
Strikingly close to the CAISO (0.047 / 0.46) and NYISO (0.053 / 0.68) hot-limb
fits — the same simple-cycle-peaker reliability-commitment physics.

**Cold limb — COAL & ST_GAS, winter peaks HB6-9+17-20, per-group T0 on TMIN**

```
COAL:    T0 = +5 °C, slope_per_c = 0.0306, cap (p97) = 1.000, ρ = +0.35
ST_GAS:  T0 =  0 °C, slope_per_c = 0.0351, cap (p97) = 1.000, ρ = +0.40
neiso_coldsnap_floor_slope_per_c = 0.0328   (mean of the two cold-limb slopes)
neiso_coldsnap_floor_cap         = 1.000    (deep-cold units saturate to full availability)
```
COAL starts hardening earlier (+5 °C) than ST_GAS (0 °C); below T0 the floor
rises as `slope × (T0 − TMIN)`, clipped to the unit's full available capacity.
The cold-limb cap is 1.0 because (a) the measured cold-snap CF saturates near
full output and (b) the bin-nameplate capacity basis understates these single
units' CAMPD output, so the deep-cold ceiling is their full availability.

## Why temperature, not net-load (CLAUDE.md #10/#11)

Both limbs are **physical temperature→commitment rules**, not fits to a TWh
residual. Each is **forward-reproducible** — a forecast year pins a weather year,
hence a TMAX/TMIN series, exactly as it pins load/wind/solar — and
**condition-responsive** (hotter summers → more CT, colder winters → more
coal/steam). That is what makes them admissible in both backcast and forecast.
The cold limb is keyed to TMIN specifically (not a U-shaped TMAX) because the
ISO-NE winter run is driven by the heating-season gas-electric constraint, a
cold-temperature phenomenon with a clean monotonic cold limb (ρ ≈ 0.35-0.40),
whereas TMAX is ~uncorrelated for these units.

## Mechanism (code)

`transmission.inject_neiso_temp_reliability_floor` (called from
`run_calibration.run_year`, default-ON for NEISO in `_calibration_config`):

1. Load the archived NEISO load-weighted daily `(tmax, tmin)`
   (`eia_loader.neiso_load_weighted_temp`).
2. Hot limb: for CT_PEAKER over HB16-21,
   `frac = clip(ct_base + ct_slope·(TMAX − ct_t0), ct_base, ct_cap)`.
3. Cold limb: for COAL and ST_GAS over HB6-9+17-20,
   `frac = clip(cold_base + cold_slope·(T0_group − TMIN), cold_base, cold_cap)`
   with per-group `T0_group` (`NEISO_COLDSNAP_T0_C`).
4. Each group's hourly target = `frac × available capacity`, distributed
   cheapest-first over the group's units (each capped at availability) into the
   hour-varying `FleetArrays.min_gen` lower bound, composed with any existing
   floor via `maximum`. The LP dispatches economically above the floor, so it
   binds only on the hot-summer-evening / deep-cold-peak hours the energy-only
   merit order would otherwise leave the units off.

## Scope: why these three classes

CT_PEAKER is the meaningful hot-limb lever (1.2 GW). COAL and ST_GAS are each a
single small plant, so their TWh impact is modest, but the cold-limb mechanism
is real ISO-NE winter-reliability behaviour and is the correct structural fix for
their under-run (CLAUDE.md #1: right mechanism, not an offer-curve tune). The
CT_PEAKER under-run was floated as a possible CT-vs-CC offer-curve mispricing;
the data shows it is the same hot-day local-reliability commitment CAISO/NYISO
solved with the temperature floor, so it is fixed structurally here rather than
by retuning offers to the residual.
