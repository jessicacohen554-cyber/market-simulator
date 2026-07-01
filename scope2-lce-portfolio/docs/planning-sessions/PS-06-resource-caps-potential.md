# PS-06 — Resource Caps & Regional Potential

**Goal:** define the per-resource capacity limits and where they come from, per ISO.

## Why it matters

The user requires the ability to set a max on each resource (e.g. existing
nuclear, but also new solar/wind/offshore). Caps also keep the LP realistic — a
premium sweep without buildout limits can pick implausible single-resource
portfolios. Caps are already wired (`config.resource_caps_mw`, table
`cap_max_default_mw`); this session sets *values* and *provenance*.

## Questions to decide

1. **Cap basis.** Interconnection queue, land/siting potential (NREL reV),
   policy limits, or user-supplied? Different basis per resource.
2. **Per-ISO tables.** Provide a caps table keyed by (iso, resource) rather than a
   single default? Where stored (`data/lcoe/` or a new `data/caps/`)?
3. **Relative vs absolute.** Express caps as MW, or as a multiple of peak load /
   annual energy (portable across facility sizes)?
4. **Offshore/geo/new-nuclear availability.** Which resources are even eligible in
   which ISO (no offshore in interior ISOs, etc.)?
5. **Floors.** Committed/contracted capacity as `resource_floors_mw`.

## Inputs to review

- `config.resource_caps_mw` / `resource_floors_mw`, `resources.py` (cap
  application), `resource_costs.csv` (`cap_max_default_mw`).

## Deliverable

- ADR on cap basis and representation (MW vs load-relative; per-ISO table).
- A caps data file (if per-ISO) + loader spec for PP-02.
- Eligibility matrix (which resources per ISO).
