# Reference-price interface — step (1) validation (PJM)

**Status:** pre-LP. The neighbor-price module is built, tested, and validated
against measured data; it is **not yet wired into the dispatch LP**. This note
records what the validation showed so the step-(2) wiring is informed by it.

## What was built

A forecast-grade, ISO-agnostic neighbor reference price
(`src/market_sim/data/neighbor_price.py`), parameterized per ISO by the
`INTERFACE_NEIGHBORS` registry in `config/constants.py`. For each neighbor:

    neighbor_price[h] = (henry_hub[year] + gas_basis) × marginal_heat_rate
                        × load_shape(neighbor_load[h])

Every term is a forecast input (Henry Hub trajectory, neighbor gas basis,
neighbor EIA-930 load) or a physically-pinned structural constant (marginal
heat rate ~7.5, hurdle $3/MWh, interface limit). **Nothing is tuned to the
net-interchange target** — so reproducing the measured net export *without being
told to* is a genuine validation, not a fit.

Neighbors resolve individually where their EIA-930 load extract exists and fall
back per-neighbor to a proxy BA otherwise. PJM today: **MISO** (own extract),
**NYISO** (own extract), **Carolinas** (no `DUK` extract yet → priced on the
`SOCO` load shape). Drop in a `DUK hourly.parquet` and the Carolinas seam lights
up on its own data with no code change.

## What the validation showed (`scripts/validate_neighbor_price.py`)

Run against PJM 2023/24/25, with no LP, on three measured benchmarks:

**Before calibration** (flat 7.5 heat rate, the placeholder):

| benchmark | result |
|---|---|
| **Neighbor price *shape*** (vs actual NYISO LMP) | tracks: hourly corr +0.39 / +0.40 / +0.49 |
| **Neighbor price *level*** | far too cheap: constructed MISO $19/$16/$22 vs real ~$36/$31/$41 |
| **Seam direction** (spread sign vs measured net export) | **wrong sign**: predicts PJM imports; hit-rate 2–11% |

**After calibration** (effective heat rates anchored to each neighbor's realized
LMP — MISO 14.2, NYISO 13.1, Carolinas 13.5; hurdle $2/MWh):

| year | PJM LMP | neighbor agg | measured export-hrs | predicted | dir hit-rate | corr(spread,−netexp) |
|---|---|---|---|---|---|---|
| 2023 | $28.4 | $36.5 | 0.98 | 0.81 | **0.81** | +0.27 |
| 2024 | $29.5 | $31.6 | 0.96 | 0.68 | **0.69** | +0.25 |
| 2025 | $42.9 | $41.2 | 0.95 | 0.62 | **0.63** | +0.01 |

Anchoring the neighbor to its own realized LMP flips the seam to correctly
predict PJM **export** in the majority of hours (was ~0). The remaining gap
between predicted (62–81%) and measured (95–98%) export hours is a **structural
export floor** — PJM exports scheduled/firm baseload (nuclear that can't back
down, bilateral contracts) even in hours when its price is at or above the
neighbor's. A pure economic price-spread captures the economic majority, not
this floor; step (2) handles it explicitly (a small must-export floor, or
accepting the economic portion) rather than inflating the heat rate to fake it.

### The headline finding (corrected after a literature check)

**The price-spread mechanism is correct and standard; the failure was that the
neighbor price was built too cheap.** A first reading of the validation —
"the spread predicts imports, so PJM's export isn't price-driven" — is *wrong*,
and an external check shows why:

* The field is unanimous that PJM↔neighbor flows follow price spreads net of a
  transaction (hurdle) cost, and that PJM is a structural net *exporter* because
  its resource mix (coal retirements + efficient new CCs, generation near load)
  makes **PJM's LMP lower than its neighbors'**. PJM's 2024 State of the Market
  report and the ACORE / PJM-MISO joint studies say exactly this.
* The numbers confirm the *direction*: MISO's 2024 average real-time LMP was
  **$31/MWh** (Potomac Economics, MISO IMM) vs PJM's ~$29.5 — and ~$36 (MISO)
  vs $28 (PJM) in 2023. So MISO really is the dearer region, and the measured
  net export shrinks as the spread shrinks (+40 TWh in 2023's wide spread →
  +18 TWh in 2025's narrow one).
* Our **constructed** MISO price was **$16 (2024)** — roughly half the real $31.
  The flat 7.5 MMBtu/MWh heat rate and the mean-preserving linear load shape
  reproduce only the gas-*burn* floor; they omit the marginal-unit inefficiency,
  congestion, and scarcity that lift a real RTO's LMP well above gas×7.5. With
  the neighbor mis-priced below PJM, the spread sign flips and the seam predicts
  imports.

So the lesson is not "abandon the spread" — it is "**price the neighbor to its
own realized LMP, not to a bare gas-burn floor**." The shape mechanism is
already sound (hourly corr +0.4 vs actual NYISO LMP); only the level is wrong.

### The fix (now implemented) — calibrate the level to the neighbor, NOT to the flow

The faithful lever is a **per-region marginal heat rate** (and possibly
supply-curve convexity, `load_shape_exponent` > 1) that makes each neighbor's
reference price reproduce *that neighbor's own* annual LMP — MISO ≈ $31 (2024),
etc. This is admissible under rule #11: the anchor is the neighbor's measured
price formation (a reproducible physical/market quantity that responds to
forward gas and load), **never PJM's net-MWh flow**. MISO and the Southeast are
the clean gas-marginal anchors; NYISO downstate is congestion-dominated (implied
HR ~10→18 across 2023-25) and a poor heat-rate anchor — keep its residual as a
documented congestion premium rather than chasing it with HR.

This is now in the `INTERFACE_NEIGHBORS` registry: MISO 14.2, NYISO 13.1,
Carolinas 13.5 MMBtu/MWh, hurdle $2/MWh (the OMS-RSC inter-RTO wheeling adder;
PJM exports at thin spreads, so the hurdle must stay small). The validation
table above is the result.

### Open items for step (2) — the LP wiring

1. **Structural export floor.** The economic spread predicts 62–81% export
   hours vs the measured 95–98%; the ~15–30 pt residual is PJM's
   scheduled/firm baseload export. Handle it explicitly (a small must-export
   floor on the seam, or accept the economic portion) — never by inflating the
   heat rate to fake the floor.
2. **NYISO year-instability.** Its implied HR runs 9.8→13.1→17.7 (2023-25)
   because downstate congestion/scarcity dominates; the single 13.1 anchor
   overshoots 2023 ($40 vs actual $30) and undershoots 2025 ($45 vs $61). NYISO
   is the smallest seam (EMAAC only), so the aggregate impact is limited, but a
   congestion premium or year-grounded NY anchor is the eventual refinement.
3. **Carolinas LMP.** The 13.5 HR is a SERC-bilateral estimate on the SOCO
   proxy; replace with a Duke (DUK) extract + realized LMP when available.

Hurdle rate: production-cost models use ~$2/MWh wheeling/transaction adders on
inter-RTO transactions (OMS-RSC seams study), matching the registry default.

This is consistent with the prior fitted `EXPORT_TRANCHES`, which reproduced
PJM's export only by pricing the export sinks at the *neighbors' avoided cost*
($16–36/MWh) — i.e. the neighbors' marginal price, which the flat-HR reference
price undershoots. The reference-price interface replaces that fit with the
neighbor's *own* gas+load+HR price, anchored to its measured LMP level.

### Sources

* PJM 2024 State of the Market (Monitoring Analytics), §9 Interchange.
* "Billions in Benefits: Expanding Transmission Between MISO and PJM" (ACORE,
  2023) and the PJM/MISO Joint Modeling Case Study — PJM net-exporter rationale.
* 2024 MISO State of the Market Report (Potomac Economics): MISO RT LMP $31/MWh.
* OMS-RSC Seams Study — Interface Pricing (SPP/MISO IMM): hurdle/wheeling
  adders (~$2/MWh) for inter-RTO transactions in production-cost models.

## Files

- `src/market_sim/data/neighbor_price.py` — the module (pure, no LP).
- `src/market_sim/config/constants.py` — `NeighborInterface`, `INTERFACE_NEIGHBORS`.
- `scripts/validate_neighbor_price.py` — the validation report.
- `tests/test_neighbor_price.py` — 15 unit + integration tests.
