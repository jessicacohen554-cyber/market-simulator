# PS-09 — Gas CC + CCS as a Portfolio Resource (backlog)

**Goal:** add carbon-capture-retrofitted (or new-build) gas combined-cycle as a
procurable firm low-carbon resource in the catalog.

**Origin:** stakeholder request 2026-07-01 — "if we do not have an option for CCS
on CC regular plants, we will need to build that eventually."

## Why it matters

Gas-CC+CCS is the main *dispatchable* low-carbon option besides
nuclear/geothermal, and often the marginal technology for the last increments of
hourly matching. Unlike every current catalog resource it is (a) fuel-burning —
its variable cost moves with gas price — and (b) **partially** clean (~90–95%
capture), so it forces a matching-credit decision the current binary
clean/not-clean framing doesn't have.

## Questions to decide

1. **Matching credit.** Does a 95%-capture MWh count as 0.95 matched MWh
   (carbon-intensity-weighted matching, interacts with ADR 0007's volumetric
   definition) or fully matched below an intensity threshold? This generalizes
   the metric to `Σ_t Σ_r credit_r · gen_serving_load_{r,t} / Σ_t load_t`.
2. **Cost structure.** ATB Gas-CC-CCS capex/FOM via ADR 0004's CRF treatment,
   plus a **fuel-dependent VOM**: heat_rate × gas_price + capture VOM. Where does
   the gas-price input come from (config scalar per run vs the market-sim
   forecast's gas path)?
3. **Residual & upstream emissions.** Count residual (uncaptured) CO₂ in
   `residual_co2_tons`? Include upstream methane in the intensity number?
4. **45Q / policy credits.** Net the 45Q capture credit out of the variable cost?
   Vintage/duration limits?
5. **Eligibility & caps.** Which ISOs (CO₂ storage geology / pipeline access);
   per-ISO caps basis.
6. **New-build vs retrofit.** One resource (new-build CCS) or also a cheaper
   retrofit tranche mirroring market-sim's §5.6 retrofit screen?

## Deliverable

- ADR on matching credit for partial-capture resources, cost/fuel structure, 45Q
  treatment, and eligibility.
- New `gas_cc_ccs` row(s) in `resource_costs.csv` (needs a fuel-price config
  field), caps rows, and — if intensity-weighted matching is adopted — an LP/
  metric extension pack (PP-08).

## Status

Backlog — deliberately **not** gating Waves 1–2. Run this session after the
current build waves land.
