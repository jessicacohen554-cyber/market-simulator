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
| — | Resource pricing / LCOE → fixed+VOM | proposed | PS-01 | PP-02 |
| — | Premium definition & excess-resale netting | proposed | PS-02 | PP-04/PP-06 |
| — | Storage costing (power/energy split, LDES, H₂) | proposed | PS-03 | PP-02 |
| — | Matching semantics (annual vs strict 24/7; carbon) | proposed | PS-04 | PP-04 |
| — | Existing-resource treatment & additionality | proposed | PS-05 | PP-02 |
| — | Resource caps & regional potential | proposed | PS-06 | PP-02 |
| — | Load intake & growth application | proposed | PS-07 | PP-01 |
| — | LMP coupling & scenario selection | proposed | PS-08 | PP-01 |

Add the assigned number when each session's ADR is written.

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
