# 0009 — Resource caps & regional potential

- **Status:** provisional (stakeholder deferred; default-decisions table applied)
- **Date:** 2026-07-01
- **Session:** PS-06 (Resource Caps & Regional Potential)
- **Implemented by:** PP-02

## Context

Capacity limits per resource keep the LP realistic — a premium sweep without
buildout limits can pick implausible single-resource portfolios. Caps are already
wired (`config.resource_caps_mw`); this session sets values and provenance per
ISO and resource type.

## Options considered

1. **Single scalar default** — one cap_mw per resource, all ISOs — too coarse;
   potential varies dramatically by region.
2. **Per-ISO table** — (iso, resource, cap_mw) matrix; portable, flexible,
   documentable (chosen).
3. **Load-relative caps** — MW as a multiple of peak/annual — harder to
   cross-ISOs; reserved for future if needed.

## Decision

**Caps are a per-(ISO, resource) table in MW**, stored at `data/caps/resource_caps.csv`
(columns: iso, resource, cap_mw, basis, notes). **Absolute MW basis** — portable
since caps encode ISO-level potential, and MW is what the LP bounds. **Basis
documented** in the table's basis/notes columns: interconnection-queue scale for
near-term techs (solar, wind), resource potential for geothermal/offshore, and
contractable-fleet share for existing nuclear/hydro. **Eligibility:** a resource
absent from an ISO's rows (or cap_mw = 0) is ineligible. Offshore wind only in
coastal ISOs (CAISO, NYISO, NEISO, PJM); geothermal only where resource exists
(CAISO; token elsewhere); existing nuclear/hydro per ISO fleet. `config.resource_caps_mw`
and `resource_floors_mw` remain per-run overrides layered on the table.

## Consequences

- New file: `data/caps/resource_caps.csv` with per-ISO, per-resource rows.
- PP-02 adds a loader for the caps table and wires eligibility checks into
  resource initialization.
- Offshore/geothermal/existing-resource regional eligibility is documented in the
  table notes; code enforces via zero-cap for ineligible combinations.
