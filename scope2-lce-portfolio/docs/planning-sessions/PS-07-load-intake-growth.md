# PS-07 — Load Intake & Growth
**DECIDED → [ADR 0010](../decisions/0010-load-intake-growth.md) (2026-07-01)**

**Goal:** finalize the load-intake contract (facility→ISO aggregation) and how
load growth is applied.

## Why it matters

Intake is facility- and/or ISO-level; the tool must aggregate to one hourly
vector per ISO. Growth turns a historical/observed 8760 into a forward load. Both
are currently minimal (`intake.py`): straight sum by (iso, hour) and a uniform
`(1+rate)^years` multiplier.

## Questions to decide

1. **Aggregation.** Sum is fine for co-located load, but do facilities in
   different ISOs need separate runs (yes) — confirm the multi-ISO workflow (one
   sweep per ISO). Any weighting/loss adjustments?
2. **Growth shape.** Uniform scaling (current) vs shape-shifting growth
   (electrification/EV/DC load changing the curve)? CAGR vs explicit per-year
   trajectory? Per-facility growth rates?
3. **Calendar alignment.** Hour indexing, leap years, timezone/DST — how is the
   8760 defined and must load & LMP share the same convention?
4. **Multiple facilities, one buyer.** Aggregate then match, or match per facility
   then sum? (Aggregation is cheaper and usually the intent — confirm.)
5. **Validation.** Required columns, handling of missing hours (currently
   zero-filled) — is zero-fill safe or should it error?

## Inputs to review

- `intake.py` (`load_intake`, `aggregate_by_hour_iso`, `apply_load_growth`,
  `prepare_load`), `docs/02-data-inputs.md`.

## Deliverable

- ADR on aggregation rule, growth model (uniform vs shaped; per-facility), and
  calendar convention.
- Any new `PortfolioConfig` fields (e.g. per-facility growth) + intake spec for PP-01.
