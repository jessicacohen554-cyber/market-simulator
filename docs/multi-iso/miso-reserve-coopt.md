# MISO market-wide energy + operating-reserve co-optimization

**Status:** implemented, **inert on the backcast LP** (default off; enabled via
`--energy-reserve-coopt`). MISO. The in-LP MISO analogue of the ERCOT ORDC /
PJM Primary-Reserve / NYISO RCPF co-optimization. **Zero parameters fitted to
the price residual.**
**Code:** `src/market_sim/results/scarcity.py` (`miso_reserve_coopt_inputs`),
`runner.py` (`iso == "MISO"` co-opt branch), constants
`MISO_REGULATING_RESERVE_MW` / `MISO_RESERVE_DEMAND_CURVE_MAX` /
`MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW`.
**Tests:** `tests/test_reserve_coopt.py` (`TestMisoReserveCooptInputs`,
`TestMisoReserveCooptLP`).
**Bundle:** `results/calibration/miso3_reservecoopt` (PROBE, NOT-YET).

## The published mechanism (provenance)

MISO co-optimizes energy with its market-wide operating reserves (Regulating +
Contingency = Spinning + Supplemental) in a single clearing. When cleared
market-wide reserves fall below the requirement, MISO's VOLL-anchored
Reliability-Based Demand Curve (RBDC) sets the reserve clearing price, and
through energy/reserve co-optimization that shadow price flows into the LMP —
the scarcity tail an energy-only LP cannot produce (MISO BPM-002 "Energy and
Operating Reserve Markets" / Schedule 28 / Schedule 28-A).

## Model mapping

- **Requirement** = MSSC (the Most Severe Single Contingency — the largest single
  reserve-eligible resource, `scarcity.largest_single_contingency_mw`, plant-
  aggregated common-mode, fleet-responsive) + `MISO_REGULATING_RESERVE_MW`
  (400 MW, Tier-3 estimate). ≈ 2.6 GW MSSC + 0.4 GW ≈ 3.0 GW market-wide. A
  near-constant reliability quantity, flat across hours (the hourly scarcity
  *incidence* comes from the hourly fleet availability in the shared-headroom
  RHS, the same design as the ERCOT/PJM/NYISO co-opt).
- **Demand curve** = a piecewise-linear ramp from $0 at the requirement to
  `MISO_RESERVE_DEMAND_CURVE_MAX` ($3,500/MWh, MISO's VOLL / RBDC anchor) at zero
  cleared reserve (`critical_mw = 0`), discretized into ascending reserve-
  shortfall steps. A documented stand-in for the posted stepped curve — the same
  convention as the NYISO/NEISO demand curves; verify the exact breakpoints
  against MISO Schedule 28-A (Tier-3).
- **Reserves** = the per-zone aggregate reserve-eligible thermal headroom
  (`RESERVE_FUEL_TYPES`), a single footprint-wide reserve family (not locational).
  The reserve-balance-row dual is persisted as `reserve_price` in
  `system.parquet`.

Nothing is fitted to the LMP residual: the requirement basis is a measured
reliability quantity and the curve anchors are the cited market design.

## Result — inert (the honest finding)

On `miso3_reservecoopt` (2023–25, import node on) the reserve clearing price is
**exactly $0 in all 26,280 hours of all three years**, so the energy dispatch
and duals are byte-identical to the `miso2_importnode` baseline (coal 181.18 TWh
in 2023 matches to the decimal). C2/C3a/net interchange are unchanged
(C3a ≈ −9/−17/−14%).

**Why:** the ~3 GW market-wide requirement never binds. MISO is a ~100 GW system
and the perfect-foresight energy LP holds tens of GW of idle reserve-eligible
thermal headroom in essentially every hour, far above 3 GW, so the demand curve
clears at $0. This is the **same result the PJM reserve campaign documented**
(`pjm-reserve-ordc.md`): the curve "never fires" because online/total reserve
sits 5–10× the requirement; the sub-shortage opportunity-cost band that carries
the real residual needs **per-gen** `R[g] ≤ ramp10[g]` reserve rows plus a
tighter commitment posture — memory-infeasible at MISO plant scale and blocked
on ramp-rate data absent from `FleetArrays`.

Per CLAUDE.md #1/#11 the requirement was **not** inflated and the penalty **not**
raised to make it bind — that would price scarcity MISO does not have. The
structure is the canonical correct market design and is **retained** as the
baseline (it stays in even though the residual did not move); the level miss is
carried by the next two levers.

## Next structural levers (separate sessions)

1. **Market-specific MISO coal offer curves** — MISO inherited ERCOT's generic
   take-or-pay tranche depth (committed 0.90×, econ_low 0.95×, i.e. offers below
   fuel cost). MISO is bituminous-heavy / market-bought; pricing MISO coal nearer
   fuel cost stops cheap coal flooding and displacing the gas fleet (model
   ST_GAS ≈ 0 vs actual 1–2.6 TWh/zone), lifting the marginal LMP so the priced
   seam imports. This is the C3a + interchange level lever.
2. **Firm-hydro (Manitoba) import block** — ~10–15 TWh/yr firm hydro into
   MISO-North, MISO's single largest real import, outside any gas-margin seam.
3. **Coal supply-class derivation** (`coal_supply_MISO.csv`) — aligns model &
   benchmark coal classification (fixes C1); feeds lever 1.

## How to run

```bash
.venv/bin/python scripts/run_calibration_full.py --iso MISO --year 2023 2024 2025 \
    --out-dir results/calibration/miso3_reservecoopt --energy-reserve-coopt
```
