# MISO energy/reserve co-optimization (miso3 reservecoopt) — run summary

**Determination: NOT-YET** (PROBE). The mechanism is structurally correct, live,
and sourced — but **fully inert** on this perfect-foresight LP, so C2/C3a/net
interchange are unchanged from miso2. Per CLAUDE.md #1 the structure **stays in**
(it is the canonical correct market structure — energy/reserve co-optimization);
the level miss is the next, separate lever, not a reason to revert or to inflate
this requirement.

## What this run adds vs miso2 importnode
An **in-LP market-wide energy + operating-reserve co-optimization for MISO**
(`scarcity.miso_reserve_coopt_inputs`, the MISO analogue of the existing
ERCOT/PJM/NYISO co-opt). MISO co-optimizes energy with its market-wide operating
reserves (Regulating + Contingency) against a VOLL-anchored Reliability-Based
Demand Curve; when cleared reserves fall below the requirement the demand curve
sets the reserve clearing price and, through co-optimization, that dual lifts the
energy LMP — the scarcity tail an energy-only LP cannot produce. A single
footprint-wide reserve family (like PJM's RTO-wide clearing), not locational.

Sourced inputs (nothing fitted to the LMP residual, CLAUDE.md #1/#12):
- **Requirement** = MSSC (Most Severe Single Contingency, the largest single
  reserve-eligible resource, **fleet-derived** via `largest_single_contingency_mw`
  so it is forecast-responsive) + `MISO_REGULATING_RESERVE_MW` (400 MW, Tier-3).
  ≈ 2.6 GW MSSC + 0.4 GW reg ≈ 3.0 GW market-wide.
- **Demand curve** = VOLL-anchored, `MISO_RESERVE_DEMAND_CURVE_MAX` = $3,500/MWh
  (MISO's VOLL / Reliability-Based Demand Curve anchor, MISO Schedule 28-A;
  Tier-3, verify exact stepped breakpoints), linearised from $0 at the
  requirement to the max at zero cleared reserve (`critical_mw = 0`) — the same
  documented stand-in used for the NYISO/NEISO demand curves.

Wiring: `--energy-reserve-coopt` → runner `iso == "MISO"` branch; the import node
(reference-price interface) stays default-on. ERCOT/PJM/NYISO byte-identical.

## Result (model vs EIA-930 actual) — INERT
| metric (model) | 2023 | 2024 | 2025 |
|----|----:|----:|----:|
| **reserve_price** (every hour) | **$0.00** | **$0.00** | **$0.00** |
| system mean LMP | 28.86 | 25.57 | 36.89 |
| miso2 mean LMP | ~28.7 | ~25.5 | ~36.8 |
| actual LMP | 31.79 | 30.80 | 42.85 |
| max LMP | 44.29 | 40.32 | 68.66 |
| net interchange (EIA +=export) | +0.1 | −7.5 | +45.0 |
| miso2 net interchange | +0.1 | −7.5 | +45.0 |
| actual net interchange | −37.91 | −23.08 | −18.96 |

The reserve clearing price is **exactly $0 in all 26,280 hours of all three
years**, so the energy dispatch and duals are identical to miso2 (coal 181.18 TWh
in 2023 matches miso2 to the decimal). C3a stays ≈ −9/−17/−14%; net interchange
does not move.

## Why it is inert — the diagnosis (CLAUDE.md #1/#11, root cause not buried)
The ~3 GW sourced market-wide requirement **never binds**: MISO is a ~100 GW
system and the perfect-foresight energy LP holds tens of GW of idle reserve-
eligible thermal headroom in essentially every hour, far above 3 GW, so the
reserve demand curve clears at $0 and adds nothing to the energy LMP. This is the
**same result the PJM reserve campaign documented**
(`docs/multi-iso/pjm-reserve-ordc.md`: the vertical step "never fires" because
online/total reserve sits ~5–10× the requirement; the residual lives in the
sub-shortage opportunity-cost band, which needs **per-gen** `R[g] ≤ ramp10[g]`
reserve rows + a tighter commitment posture — memory-infeasible at plant scale
and blocked on ramp-rate data absent from `FleetArrays`).

Per CLAUDE.md #1/#11 the requirement was **not** inflated and the penalty **not**
raised to manufacture a binding shortage — that would price scarcity the market
does not have. The honest finding is that MISO's market-wide reserve demand curve
cannot self-target the broad level miss on this LP; the structure is retained as
the correct baseline, and the level is carried by the next two levers.

## Next levers (handed off to parallel sessions)
1. **Market-specific MISO coal offer curves** (the level lever for C3a + the
   seam). MISO inherited ERCOT's generic-COAL take-or-pay tranche depth
   (committed 0.90×, econ_low 0.95× — offers below fuel cost). MISO is
   bituminous-heavy / market-bought; market-specific curves that price MISO coal
   nearer fuel cost stop cheap coal flooding and displacing the gas fleet (model
   ST_GAS ≈ 0 vs actual 1–2.6 TWh/zone), lifting the marginal LMP so the seam
   imports.
2. **Firm-hydro (Manitoba) import block** — the ~10–15 TWh/yr of firm hydro into
   MISO-North is MISO's single largest real import and is outside any gas-margin
   seam; a firm-import block priced as firm hydro is the documented way to close
   the interchange gap (model imports only 21–58% of hours vs actual 79–98%).
3. **Accurate-data coal supply-class derivation** (`coal_supply_MISO.csv`) — fixes
   the C1 benchmark misclassification (model coal currently all generic vs the
   benchmark's PRB/BIT split); expected to make C3a slightly *worse* (routes
   MISO-North PRB plants onto the cheaper COAL_PRB curve), which per CLAUDE.md #13
   exposes the ERCOT COAL_PRB curve as too cheap for MISO — feeds lever 1.
