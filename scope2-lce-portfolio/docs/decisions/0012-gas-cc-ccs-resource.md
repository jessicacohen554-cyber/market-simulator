# 0012 — Gas CC + CCS as a portfolio resource; low-carbon threshold credit

- **Status:** accepted (stakeholder-decided 2026-07-02)
- **Date:** 2026-07-02
- **Session:** PS-09 (Gas CC + CCS as a Portfolio Resource)
- **Implemented by:** PP-08

## Context

Gas-CC+CCS is the main dispatchable low-carbon option besides nuclear and
geothermal. Unlike every current catalog resource it is fuel-burning (variable
cost moves with gas price) and only *partially* clean (~90–95% capture), which
forces a matching-credit rule the binary clean/not-clean framing didn't have.

## Options considered

1. **Intensity-weighted credit** — each MWh counts as `capture_rate` matched.
   Most granular; complicates the volumetric metric.
2. **Threshold full credit (chosen)** — counts fully as low-carbon matching if
   it clears a bright-line intensity/capture test; emissions still reported.
3. **Energy-only** — never counts toward matching; makes CCS pointless here.

## Decision

- **Matching credit:** a resource counts **fully** toward hourly matching iff
  `capture_rate > 0.90` **and** residual emission factor `< 0.050 tCO₂/MWh`
  (50 kg/MWh). This is *low-carbon* electricity matching — qualifying CCS output
  is not discounted in the matching metric. A fossil resource failing either
  test is not admissible to the catalog as a matching resource.
- **Emissions are still counted:** the catalog gains a per-resource
  `emission_rate_ton_mwh` column (0 for all existing resources; CCS residual =
  `(1 − capture_rate) × pre-capture intensity`). Reported residual carbon
  generalizes to `residual_co2_tons = grid_buy_mwh × marginal_rate +
  Σ_r gen_r × emission_rate_r` (extends ADR 0007; reporting only, no LP change).
- **Gas price:** per-ISO **delivered** gas prices at the same fidelity the
  market-simulator LP uses (zonal/citygate where available): a cited
  `data/fuel/gas_prices.csv` table (iso, price_mmbtu, basis, notes), values
  consistent with the market sim's fuel representation for the modeled year;
  `vom_fuel = heat_rate × delivered price`. Config override per run.
- **45Q:** on by default — variable cost is net of
  `capture_rate × pre-capture intensity × ccs_45q_per_ton` (new config field,
  default 85 $/tCO₂, cited; 0 disables).
- **Scope: both tranches now** — `gas_cc_ccs_new` (ATB Gas-CC-95%-CCS
  capex/FOM/heat-rate via the ADR 0004 CRF treatment) and `gas_cc_ccs_retrofit`
  (lower capex on an existing CC; per-ISO cap tied to the existing CC fleet,
  mirroring the `nuclear_existing` contractable-share logic in ADR 0009).

## Consequences

- Catalog schema gains `emission_rate_ton_mwh`, `heat_rate_mmbtu_mwh`,
  `capture_rate` columns; new `data/fuel/gas_prices.csv`; caps rows for both
  tranches per ISO (CO₂ storage/pipeline eligibility documented in `basis`).
- `resources.py` computes the net VOM (fuel + capture VOM − 45Q); the threshold
  test is enforced at load time with a clear error.
- Residual-CO₂ reporting extends to resource emissions (outputs + lp result).
- Deferred: hour-varying gas prices; upstream methane in the intensity number;
  45Q vintage/duration limits (flat credit for now, noted in citations).

## Amendment note (2026-07-02, audit finding DL-12)

The 45Q credit is netted into variable cost with a **floor at $0/MWh net
VOM** (`resources.py`): at delivered gas below ~$2.26/MMBtu the credit would
exceed fuel + VOM, and a negative net variable cost would pay the LP to
generate into the excess path to farm the credit — the real credit is
bounded by actually-stored tonnage, and modeling sub-zero variable cost is
out of scope. Consequences: below that breakeven the resource's dispatch
cost is flat at $0 (gas-price sensitivity is deliberately erased in a region
none of the shipped delivered prices enter), degenerate with true-zero-VOM
resources up to the solver's tiebreaks. This documents the clamp already
implemented at load time; audit verification confirmed it never binds with
the shipped gas-price table.
