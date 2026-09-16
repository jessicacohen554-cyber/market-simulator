# nwpp-wind-shape — raw

`nwpp_<year>_wind_zone_shape.parquet` (**2023–2025**) — per-zone hourly wind
SHAPE for NWPP's five model zones, and the first one in this repo that is
**MEASURED rather than modelled**.

Opened **2026-09-14** by lane **NWPP-33**
(`docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-33; FINDING
`docs/handoffs/FINDING-nwpp-33-2026-09-14.md`).

## Why this one is measured and MISO's / SPP's / ERCOT's are not

Those three get their per-zone wind shape from MERRA-2 reanalysis wind speed at
each plant, run through a turbine power curve (`scripts/lib/wind_shape.py`),
because EIA-930 publishes their wind as ONE BA-wide series that cannot be taken
apart. **NWPP is a pool of seventeen balancing authorities, EIA-930 publishes
`NG: WND` separately for every one of them, and owner ruling N5 makes every model
zone a whole-BA group** — so each zone's hourly wind output is a plain sum of
published series. Under rule 14 `[R-ACCURATE]` a measured series beats a
modelled one, so this builder reads rather than simulates, and it carries none
of the reanalysis path's physics constants (no shear exponent, no power curve,
no hub height): **zero free parameters** (rules 21 `[R-DOF]` / 24
`[R-REGISTRY]`).

## Schema and clock

`hour` (int64, 0–8759 on the fixed non-leap clock) plus one float64 column per
model zone — exactly the schema `renewables._wind_zone_reanalysis_shapes` reads
for MISO / SPP / ERCOT, and the filename is exactly what it composes from
`paths.wind_shape_dir("NWPP")`, so arming needs no new parsing code.

Row `k` is pool-clock hour `k`: `eia930.frames._pool_member_frames` re-indexes
every member onto the `_POOL_CLOCK_BA` (BPAT) **Pacific** local year by a pure
UTC join, so the three Mountain members (NWMT, PACE, WAUW) land on the Pacific
hour that is the same physical hour. **UTC is the canonical key and local time
is provenance only** (card N6, gate G19). This is the same positional clock the
system demand, the zonal shares and the dispatch use.

Values are the zone's implied hourly capacity factor: measured generation
clipped at zero, over the zone's EIA-860 **December** operable capacity from
`renewables._eia860_monthly_capacity` — the same denominator the consumer
weights zones by, assigned through the same `_NWPP_BA_ZONES` key, so numerator
and denominator are attributed on one key.

## What the measurement says

Night(00-06)/afternoon(12-18) ratio by zone, 2023 / 2024 / 2025:

| Zone | ratio | fleet CF (2024) |
|---|---|---:|
| **NWPP-OR** | **1.26 / 1.26 / 1.32** — nocturnal | 0.384 |
| NWPP-INLAND | 1.07 / 1.10 / 1.08 | 0.402 |
| NWPP-NW | 0.89 / 0.82 / 0.82 | 0.248 |
| NWPP-EAST | 0.82 / 0.86 / 0.85 | 0.296 |
| **NWPP-SNV** | **0.55 / 0.59 / 0.57** — afternoon | 0.241 |

A **2.3× spread**, stable in sign and rank across all three years. The contrast
that justified SPP's own per-zone wind shape was 1.04 vs 0.97 — a 7 %
difference.

**AVRN and GRID carry real wind and it lands with their balancing authority:**
AVRN 5.3 TWh in 2024 (a third of NWPP-NW's total) and GRID 2.2 TWh (over half of
NWPP-OR's). They serve no load, but they are not empty on the supply side.

EIA-930 posts a few small negative wind hours (station-service netting); they
are clipped to zero, which is what `renewables` does at read time anyway, and
the effect is ≤ 0.02 % of any zone-year's positive energy. **Nothing is padded,
interpolated or rescaled** (rule 13 `[R-MEASURED]`).

## Regeneration

`python scripts/data/build_nwpp_vre_shape.py --fuel wind`
(defaults to 2023 2024 2025; `--dry-run` reports without writing).

Inputs are all committed: the seventeen `data/raw/eia-930-hourly/<BA> hourly.parquet`
extracts (landed by NWPP-11) and `data/raw/eia-860/eia860_wind_operable.parquet`.
A year needs a complete 8760-hour extract for every member — `_pool_member_frames`
returns `None` on a subset and the builder skips that year rather than serving a
partial footprint, which is why 2026 (H1 only) is not buildable.

## NOT ARMED

Nothing reads these files yet: `paths.WIND_SHAPE_DIRS` carries no `NWPP` entry
and `renewables._WIND_ZONE_SHAPE_ISOS` no `NWPP` membership. Both live under
`src/`, outside lane NWPP-33's boundary, so no `cache_key` moves, no existing
keeper is touched and no `ScenarioConfig` field was added (plan §7 gate G8).
Arming is routed to NWPP-DESK — see the FINDING §5.
