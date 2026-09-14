# nwpp-solar-shape — raw

`nwpp_<year>_solar_zone_shape.parquet` (**2023–2025**) — per-zone hourly solar
SHAPE for NWPP's five model zones, measured off the per-BA EIA-930 `NG: SUN`
series.

Opened **2026-09-14** by lane **NWPP-33**
(`docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-33; FINDING
`docs/handoffs/FINDING-nwpp-33-2026-09-14.md`).

Method, schema, clock and conventions are **identical to the sibling
`nwpp-wind-shape/`** — read that README; only the fuel column differs
(`NG: SUN` over `NG: WND`, EIA-860 solar operable capacity as the denominator).

## What the measurement says

Solar's diurnal contrast is not a night/afternoon ratio — it is **when the day
peaks**. The energy-weighted mean hour-of-day of solar output, on the pool's
Pacific clock:

| Zone | 2023 | 2024 | 2025 | fleet CF (2024) |
|---|---:|---:|---:|---:|
| NWPP-NW | 11.81 | 11.88 | 11.74 | 0.073 |
| NWPP-OR | 11.30 | 11.35 | 11.36 | 0.233 |
| NWPP-SNV | 11.21 | 11.17 | 11.13 | 0.225 |
| NWPP-INLAND | 11.05 | 11.05 | 11.06 | 0.210 |
| NWPP-EAST | 10.81 | 10.83 | 10.87 | 0.293 |

A **one-hour west-to-east progression in exactly the geographic order**,
reproducing to ±0.07 h across three independent years — which is what a
footprint spanning ~11° of longitude and two timezones must produce, and is the
cleanest available check that these series are the real thing rather than noise.
`NWPP-EAST` (Utah / Wyoming, filed on Mountain time) peaks a full hour earlier
on the Pacific clock than `NWPP-NW`.

**`NWPP-NW`'s solar CF of 0.073–0.083 is real, not a defect.** That zone's
475–773 MW is the Pacific-Northwest fleet (BPAT + PSEI), the worst solar
resource in the footprint; BPAT's `NG: SUN` also carries the most negative
hours of any member (station-service netting), and clipping them costs 0.56 % of
that zone-year's positive energy — the largest clip in either fuel, and still
under 1 %.

## NOT ARMED, and unlike the wind file it has no consumer to arm

The per-zone SOLAR shape path (`renewables._SOLAR_ZONE_SHAPE_ISOS`) builds a
**clear-sky shape from EIA-860 tracking geometry and reads no file at all**, so
wiring a measured solar shape in is a design question, not a registry entry.
Lane NWPP-33 lands the measurement and routes the design to NWPP-DESK — see the
FINDING §5. No `cache_key` moves and no `ScenarioConfig` field was added.

## Regeneration

`python scripts/data/build_nwpp_vre_shape.py --fuel solar`
