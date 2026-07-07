# 0021 — Breakeven EAC derivation (PPA-strike logic, capacity + 45Q offsets)

- **Status:** accepted
- **Date:** 2026-07-07
- **Session:** scope-2 EAC diagnosis + wiring
- **Implemented by:** `scripts/derive_eac_breakeven.py` (default-off helper)

## Context

For an attribute-basis (`lmp_ppa`, ADR 0020) resource — especially CCS — the EAC
premium is not a free number. The owner framed it precisely: the price must be
the all-in energy + capacity + 45Q + EAC that clears the developer's IRR/NPV
hurdle on the capex — i.e. the residual $/MWh the project needs *after every
other revenue stream*. That is exactly how a wind/solar PPA strike is set, so one
calculation serves wind, solar, and CCS.

## Options considered

1. **Guess/administrative EAC values** — a fitted knob. Rejected: no forward
   analogue, violates the "reproducible input, not the answer" discipline.
2. **Endogenous LP capex recovery** (build basis) — works for merchant build but
   not for "buy the attribute at LMP + premium"; and for CCS the owner wants
   capex/45Q kept with the project, not in the buyer's LP.
3. **A standalone breakeven derivation that produces the EAC input** — chosen.

## Decision

`breakeven_eac = max(0, required_all_in − offsets)`, where

    required_all_in ($/MWh) = CRF(hurdle, term)·capex($/kW)·1000/(8760·CF)
                            + FOM($/kW-yr)·1000/(8760·CF) + VOM + fuel
    offsets ($/MWh)         = expected LMP capture + 45Q/MWh + capacity/MWh

- **45Q accrues to the project owner**, so it is a *revenue offset* that lowers
  the buyer's EAC — never netted into the LP VOM (ADR 0020).
- **Capacity revenue** offsets the EAC only where a capacity market exists. The
  per-ISO `CAPACITY_PRICE_KW_YR` registry mirrors the market simulator's
  `MARKET_DESIGN` split: ERCOT is energy-only (0); PJM/NYISO/NEISO/MISO/CAISO
  carry net-CONE-style anchors.
- The helper is **default-off** — it never runs inside the LP. Its output is the
  flat/annual number fed into `data/eac/eac_prices.csv`, a reproducible
  forward-driver-derived input.

## Consequences

- One code path derives PPA-style premiums for wind/solar (no fuel/45Q) and CCS
  (all terms).
- The shipped `eac_prices.csv` values are illustrative until regenerated per ISO
  with real expected-LMP captures and auction/RA capacity prices.
- Deferred: wiring the helper to read the cost table + a forecast LMP export and
  emit `eac_prices.csv` rows directly (currently a manual CLI step).
