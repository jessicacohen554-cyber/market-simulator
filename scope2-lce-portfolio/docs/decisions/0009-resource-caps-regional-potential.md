# 0009 — Resource caps & regional potential

- **Status:** amended & ratified (stakeholder session 2026-07-02) — cap VALUES
  ratified as-is; basis language amended: interconnection-queue scale plays NO
  role in this tool. See Amendment below.
- **Date:** 2026-07-01 (amended 2026-07-02)
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
documented** in the table's basis/notes columns: ~~interconnection-queue scale
for near-term techs (solar, wind)~~ *(amended 2026-07-02 — see below)* resource
potential for all new-build techs (solar, wind, geothermal, offshore, storage),
and contractable-fleet share for existing nuclear/hydro. **Eligibility:** a resource
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

## Amendment (stakeholder ratification session, 2026-07-02)

**Cap values ratified as-is** — session evidence-check verified the fleet-share
rows against actual fleets (PJM ~32 GW nuclear, MISO ~12 GW, NYISO ~3.4 GW,
NEISO ~3.3 GW, ERCOT ~4.9 GW, Diablo Canyon ~2.2 GW; NYISO Niagara/St. Lawrence
hydro ~5 GW) and the offshore/geothermal eligibility map against lease areas
and resource geography.

**Basis language amended: the interconnection queue plays NO role in this
tool.** Stakeholder direction (paraphrased): the tool assumes all resources are
available to build or acquire to hit targets, without queue considerations —
it exists simply to identify the cheapest portfolio. Caps therefore encode
**physical/technical resource potential** (new-build techs) and
**contractable fleet share** (existing nuclear/hydro) only — never queue
position, queue scale, or interconnection timing. This matches what
`data/caps/resource_caps.csv` already records (every solar/wind row carries a
`resource-potential` basis label); the ADR's original "interconnection-queue
scale for near-term techs" sentence was the inconsistency and is struck. No
data or code change required.
