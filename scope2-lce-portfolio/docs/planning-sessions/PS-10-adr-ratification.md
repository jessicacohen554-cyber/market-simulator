# PS-10 — Stakeholder ratification of provisional ADRs 0005 / 0007 / 0009 / 0010

- **Date:** 2026-07-02
- **Participants:** stakeholder (Jessica), facilitator (Claude)
- **Scope:** ratify or amend the four decisions adopted provisionally from the
  default-decisions table. Per PLAN.md §10 the real-LMP validation runs are on
  hold, so ratification was done on **source evidence** (web research, fleet
  data, code inspection), not model output.

## Evidence reviewed

- **0005:** LBNL solar-to-grid / Pexapark capture-curve literature (renewable
  capture prices below average LMP — i.e. cannibalization shows up in *hourly*
  prices); ERCOT curtailed >8 TWh of wind+solar in 2024 (Modo Energy); basis
  risk is a nodal-vs-hub/zonal phenomenon the single-node-per-ISO tool cannot
  resolve.
- **0007:** EPA eGRID documentation (non-baseload rates are for
  marginal/avoided-emission analysis and overstate Scope 2 for general
  consumption); GHG Protocol Scope 2 Guidance (location-based method uses
  *average* factors); NREL Cambium LRMER is likewise a consequential metric —
  corroborates ADR 0013's stakeholder correction.
- **0009:** fleet-share cap rows checked against actual fleets (PJM ~32 GW
  nuclear, MISO ~12, NYISO ~3.4, NEISO ~3.3, ERCOT ~4.9, Diablo Canyon ~2.2 GW;
  NYISO Niagara/St. Lawrence hydro ~5 GW); offshore-wind eligibility vs BOEM
  lease areas; geothermal vs resource geography. Found the ADR text/CSV basis
  mismatch (queue-scale wording vs `resource-potential` labels).
- **0010:** `intake.py` inspected — error-on-missing-hours, duplicate-row and
  column validation, non-leap LST calendar, uniform shape-preserving growth all
  implemented as written.

## Outcomes

| ADR | Outcome | Decision |
|---|---|---|
| 0005 | **Amended** | Surplus credited at **full hourly ISO-average LMP** (`excess_sale_fraction` default → **1.0**). Rationale: hourly LMP valuation already embeds cannibalization; with no locational precision on project siting, the ISO-average hourly price (the ADR 0011 series the tool already consumes) is the right credit — no separate basis/curtailment haircut. Knob retained for sensitivities. |
| 0007 | **Ratified** (remaining provisional half) | Storage provenance stands: grid purchases counted unmatched at purchase time, no round-trip laundering. ADR 0013 supersession of the carbon half confirmed. |
| 0009 | **Amended & ratified** | All cap VALUES ratified. Basis language amended: **the interconnection queue plays no role** — the tool assumes all resources are buildable/acquirable and simply finds the cheapest portfolio; caps encode physical resource potential + contractable fleet share only (matching the CSV's existing labels). |
| 0010 | **Ratified** | No load growth by default; uniform same-shape growth knob retained; error-on-missing-hours, non-leap LST calendar confirmed. |

## Follow-up build items

1. **(from 0005)** Change `PortfolioConfig.excess_sale_fraction` default
   `0.75 → 1.0` in `src/lce_portfolio/config.py`; update the field docstring
   (full-LMP + ISO-average rationale) and any tests/examples that assume 0.75.
   Deliberately NOT applied in this session (docs-only ratification).

No other code or data changes required — 0009's amendment matched the data
already on disk, and 0007/0010 were ratified as implemented.
