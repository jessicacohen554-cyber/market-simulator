# 0010 — Load intake & growth application

- **Status:** provisional (stakeholder deferred; default-decisions table applied)
- **Date:** 2026-07-01
- **Session:** PS-07 (Load Intake & Growth)
- **Implemented by:** PP-01

## Context

Facilities must be aggregated to one hourly load vector per ISO, and historical
load must be grown forward to the study year. The intake contract (facility schema,
missing-hour handling, calendar convention) and growth model (uniform vs shaped)
shape the dispatch and must be consistent across all sweeps.

## Options considered

1. **Aggregate then match** (per-ISO sum, one sweep) — economical, matches real
   procurement intent (chosen).
2. **Match per facility, sum results** — finer-grained but noisier and slower.
3. **Shaped growth** (per-facility, sector-specific) — realistic but requires
   forecasts; deferred to v2.

## Decision

**Aggregation:** facilities are summed within (iso, hour); one sweep per ISO;
aggregate-then-match is the default (portfolio serves the combined load). Multi-ISO
studies run separate per-ISO sweeps. **Growth:** uniform scaling load ×
(1+rate)^years, where rate = `config.load_growth_rate` (default 0%) and years =
number of forward years (`config.growth_years`). Shape-shifting and per-facility
growth rates deferred. **Calendar:** 8760 hours indexed 0..8759, local standard
time, non-leap convention; load and LMP files must share the same calendar
(validated: equal length, same index). **Validation:** missing hours are an ERROR
(replace current silent zero-fill); required columns (hour, iso, mwh) enforced
with clear messages.

## Consequences

- `intake.py` validates calendar alignment and rejects missing hours.
- New validation error messages for missing columns and length mismatches.
- Load growth applied uniformly at load-aggregation time (no per-facility rates yet).
- `config.load_growth_rate` and `config.growth_years` control scaling; defaults
  are 0 (no growth) and 0 (modeled year is input year).
