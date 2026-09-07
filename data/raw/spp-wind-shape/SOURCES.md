# spp-wind-shape — SOURCES

Landed 2026-09-07 by lane **SPP-32**. Every input below is public and keyless;
no credential was used and none is needed to regenerate.

## 1. NASA POWER hourly WS50M (MERRA-2 reanalysis) — the wind speed

| Field | Value |
|---|---|
| Endpoint | `https://power.larc.nasa.gov/api/temporal/hourly/point` |
| Parameter | `WS50M` (50 m wind speed, m/s) |
| Community | `RE` |
| Time standard | `UTC` |
| Auth | none (keyless) |
| Licence | Public domain (NASA open-data policy) |
| Reached | 2026-09-07, HTTP 200, 36 point-years fetched (2 zones × 6 sample points × 3 years) |

Queried once per (sample point, year) over `start=<Y>0101` … `end=<Y+1>0101`, a
window that covers the model's UTC clock for the local year.

## 2. EIA-860 wind operable schedule — the siting

Plant coordinates (`eia860_plant.parquet`: `Latitude`, `Longitude`), nameplate
(`Nameplate Capacity (MW)`), `Operating Year`, `Status == OP`, and turbine hub
height (`Turbine Hub Height (Feet)`) come from the active EIA-860 vintage
(`market_sim.config.paths.active_eia860_dir()`) — already committed, not
re-fetched by this lane. Plants are assigned to a model zone by
`market_sim.data.zone_assignment.build_zone_lookup("SPP")`, the same geography
the fleet and solar paths use, so a plant cannot land in one zone here and
another there.

Measured SPP wind fleet at the 2025 vintage (`Status == OP`):

| Zone | Plants | Nameplate |
|---|---|---|
| SPP-North | 135 | 17,664.3 MW |
| SPP-South | 119 | 17,799.1 MW |
| **Total** | **254** | **35,463.4 MW** |

Independent corroboration: SPP's own MMU reports 35,934 MW of registered wind
nameplate at end-2025 (`data/raw/spp-hsl/spp_wind_curtailment_annual.csv`,
ASOM 2025 p. 50). The 1.3 % gap is the expected EIA-860-operable vs
SPP-registered difference and no adjustment is made for it — neither number is
used as a level here.

## 3. EIA-930 `SWPP` hourly extract — the clock

`eia_loader._eia_hourly_frame_filled("SWPP", year)` supplies the `UTC time`
column; frame row *k* is model local hour-of-year *k*. The shape is placed on
that clock directly, so it lines up hour-for-hour with `cf_profile` with no
timezone assumption anywhere in the builder. SPP resolves to BA code `SWPP`
through `market_sim.data.fleet.ISO_TO_BA_CODE`.

## 4. SPP Integrated Marketplace generation mix — the reconciliation target ONLY

`data/raw/spp-genmix/GenMix_{2023,2024,2025}.csv` (landed by lane SPP-12; see
that directory's own `README.md` / `SOURCES.md` for the portal URLs and SPP's
Terms & Conditions). Delivered wind is `Wind Market` + `Wind Self` — SPP splits
every fuel into market-dispatched and self-scheduled halves and neither half
alone is the fleet's output. 5-minute intervals, `GMT MKT Interval` in UTC,
averaged to the model's hourly clock.

**This series scores the shape; it never sets it.** `--reconcile` normalises
both series to unit mean, prints three correlations, and returns; the written
parquet is byte-identical with and without the flag. Using it as a level would
be the pinning rule 13 `[R-MEASURED]` forbids — and would additionally be wrong
on its own terms, since GenMix is post-curtailment delivered wind while the
shape is an uncurtailed potential.

## 5. Physics constants — cited, not fitted

| Constant | Value | Source |
|---|---|---|
| Shear exponent | 1/7 (≈0.143) | Neutral-stability onshore power-law ("1/7th power law"); Manwell et al., *Wind Energy Explained* |
| Reanalysis height | 50 m | NASA POWER `WS50M` reference height |
| Default hub height | 90 m | Modern onshore hub, used only when EIA-860 leaves the field blank |
| Cut-in / rated / cut-out | 3 / 12 / 25 m/s | Representative IEC class II onshore turbine |
| Samples per zone | 6 | Largest plants by nameplate; captures spatial smoothing without an unbounded number of API calls |

Every one of these is **identical to the MISO and ERCOT builders by intent**. A
different shear exponent or power curve for SPP would be an unmotivated per-ISO
degree of freedom (rule 21 `[R-DOF]`) — and since only the relative shape
survives downstream, a per-ISO curve could not be identified from anything
except a residual, which rule 1 `[R-STRUCT]` forbids.

## Regeneration

    python scripts/data/build_spp_wind_shape.py --years 2023 2024 2025 --reconcile

---

## NOTE 2026-09-07 — lane SPP-54: three-zone rebuild (not landed here)

Same inputs, same builder, on the SPP-54 three-zone map (design commit `8d427adc`): SPP-North 17,664.3 MW
(unchanged), SPP-South (residual, Oklahoma + SWEPCO) 13,145.6 MW, SPP-SPS (Texas Panhandle + South Plains +
eastern NM) 4,653.5 MW; 3 zones × 6 sample points × 3 years = 54 point-years, HTTP 200 throughout. See the
README note for why the committed parquets stay two-zone.
