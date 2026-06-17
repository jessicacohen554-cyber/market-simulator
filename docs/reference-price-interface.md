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

| benchmark | result |
|---|---|
| **Neighbor price *shape*** (vs actual NYISO LMP) | tracks: hourly corr +0.39 / +0.40 / +0.49 |
| **Neighbor price *level*** (vs actual NYISO LMP) | understates: $23 vs $30, $21 vs $36, $26 vs $61 — gap widens in tight years |
| **Seam direction** (spread sign vs measured net export) | **wrong sign**: predicts PJM imports; PJM exports in 95–98% of hours; hit-rate 2–11% |

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

### Implication for step (2) — calibrate the level to the neighbor, NOT to the flow

The faithful lever is a **per-region marginal heat rate** (and possibly
supply-curve convexity, `load_shape_exponent` > 1) that makes each neighbor's
reference price reproduce *that neighbor's own* annual LMP — MISO ≈ $31 (2024),
etc. This is admissible under rule #11: the anchor is the neighbor's measured
price formation (a reproducible physical/market quantity that responds to
forward gas and load), **never PJM's net-MWh flow**. MISO and the Southeast are
the clean gas-marginal anchors; NYISO downstate is congestion-dominated (implied
HR ~10→18 across 2023-25) and a poor heat-rate anchor — keep its residual as a
documented congestion premium rather than chasing it with HR.

Hurdle rate: production-cost models use ~$2/MWh wheeling/transaction adders on
inter-RTO transactions (OMS-RSC seams study), so the $3/MWh default sits in the
right band.

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
