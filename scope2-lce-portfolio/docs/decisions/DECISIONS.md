# Decision Log (ADRs)

Running record of design decisions for the LCE portfolio tool. Each planning
session (`docs/planning-sessions/PS-*`) ends by adding a numbered ADR here (copy
`0000-template.md`). Prompt packs (`docs/prompt-packs/PP-*`) cite the ADR numbers
they implement. Keep entries short; link to the session prompt and any analysis.

## Status legend

`proposed` → `accepted` → (`superseded by NNNN`)

## Index

| # | Title | Status | Session | Implemented by |
|---|---|---|---|---|
| 0001 | Standalone/vendored coupling; no `market_sim` import | accepted | (initial) | scaffold |
| 0002 | Default mode = premium-cap → max matching | accepted | (initial) | `lp.py` |
| 0003 | IPM solver, crossover off (storage-network speed) | accepted | (build) | `lp.py` |
| 0004 | Resource pricing: pay-for-capacity from NREL ATB | accepted | PS-01 | PP-02 |
| 0005 | Premium definition & excess-resale netting | amended & ratified 2026-07-02 (full hourly ISO-avg LMP, f=1.0) | PS-02, PS-10 | PP-04/PP-06 |
| 0006 | Storage costing: tranches for Li-ion, power/energy split for LDES & H₂ | accepted | PS-03 | PP-02/PP-04 |
| 0007 | Matching semantics: volumetric hourly matching, storage provenance, residual carbon | accepted (provenance ratified 2026-07-02; carbon attribution superseded by 0013, confirmed) | PS-04, PS-10 | PP-04/PP-06 |
| 0008 | Existing-resource treatment: going-forward cost + EAC premium | accepted | PS-05 | PP-02 |
| 0009 | Resource caps & regional potential | amended & ratified 2026-07-02 (values stand; queue plays no role) | PS-06, PS-10 | PP-02 |
| 0010 | Load intake & growth application | accepted (ratified 2026-07-02) | PS-07, PS-10 | PP-01 |
| 0011 | LMP coupling & scenario selection | accepted | PS-08 | PP-01 |
| 0012 | Gas CC + CCS resource; low-carbon threshold credit (<50 kg/MWh, >90% capture) | accepted | PS-09 | PP-08 |
| 0013 | Residual carbon: hourly fossil-only average rate (attributional) | accepted | (stakeholder correction of 0007) | `intake.py`/`lp.py`/`scripts/build_fossil_avg_co2_rate.py` |
| 0014 | Reporting deliverable: self-contained HTML run report + committed `results/` store | accepted | PS-11 | PP-09 |
| 0015 | Forecast LMP selection: years 2030–2050, base-BAU scenario, readiness gate, rollout | accepted (execution on hold, PLAN.md §10) | PS-12 | none — pins `export_lce_lmp.py` args |
| 0016 | Desktop launcher: `.bat`/`.sh` twins → local HTML launch page (stdlib server, run queue + saved configs) → report | accepted | PS-13 | PP-10 |

---

## 0001 — Standalone, vendored coupling
**Status:** accepted. The tool never imports `market_sim`; it consumes the BAU
LMP file and copies any reused loader logic into `src/lce_portfolio/vendored/`
with re-sync notes. Rationale: hard isolation from the core solver.

## 0002 — Default mode: premium-cap → maximize matching
**Status:** accepted. Primary framing is "how matched for $X premium". Mode B
(matching-target → min premium) is also supported. Rationale: matches the user's
stated question and enables the premium sweep.

## 0003 — Interior-point solver, crossover off
**Status:** accepted. The 8760-hour cyclic storage-SOC network stalls the dual
simplex under heavy storage use; IPM solves in seconds and still yields row
duals. Crossover off is acceptable for reporting matching%/premium/build MW.
